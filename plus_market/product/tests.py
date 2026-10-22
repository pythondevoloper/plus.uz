from django.test import TestCase, override_settings
from django.urls import reverse

from .models import CustomUser, Category, Product, Region, Order, OrderItem, Review, Favorite

# Testlarda WhiteNoise "manifest" saqlagichi collectstatic talab qiladi — oddiy saqlagichga almashtiramiz.
PLAIN_STATIC = override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")

CHECKOUT_DATA = {"full_name": "Ali Valiyev", "phone_number": "+998901234567", "address": "Chilonzor"}


def make_user(email="user@example.com"):
    return CustomUser.objects.create_user(
        email=email, password="pass12345", full_name="User", phone_number="+998900000000")


def make_product(title="Pomidor", price=10000, stock=10, category=None):
    category = category or Category.objects.create(name=f"Kategoriya {title}")
    return Product.objects.create(category=category, title=title, price=price, stock=stock, is_available=True)


@PLAIN_STATIC
class CartAndCheckoutTests(TestCase):
    def setUp(self):
        self.region = Region.objects.create(name="Toshkent", delivery_cost=15000)
        self.p1 = make_product("Pomidor", 10000, 10)
        self.p2 = make_product("Bodring", 8000, 5, category=self.p1.category)

    def add(self, product, qty=1):
        for _ in range(qty):
            self.client.post(reverse("cart_add", args=[product.id]))

    def checkout(self):
        return self.client.post(reverse("checkout"), {**CHECKOUT_DATA, "region": self.region.id})

    def test_cart_mutations_require_post(self):
        self.add(self.p1)
        for name in ["cart_add", "cart_increase", "cart_decrease", "cart_remove"]:
            self.assertEqual(self.client.get(reverse(name, args=[self.p1.id])).status_code, 405, name)

    def test_checkout_saves_ALL_cart_items_not_just_first(self):
        self.add(self.p1, 2)
        self.add(self.p2, 3)
        response = self.checkout()

        order = Order.objects.get()
        self.assertRedirects(response, reverse("order_success", args=[order.token]))
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.items.get(product_title="Pomidor").quantity, 2)
        self.assertEqual(order.items.get(product_title="Bodring").quantity, 3)
        self.assertEqual(order.product_total, 10000 * 2 + 8000 * 3)
        self.assertEqual(order.total_amount, 44000 + 15000)

    def test_checkout_decreases_stock_and_clears_cart(self):
        self.add(self.p1, 2)
        self.add(self.p2, 1)
        self.checkout()
        self.p1.refresh_from_db(); self.p2.refresh_from_db()
        self.assertEqual((self.p1.stock, self.p2.stock), (8, 4))
        self.assertEqual(self.client.session.get("cart", {}), {})

    def test_order_item_keeps_price_snapshot(self):
        self.add(self.p1, 1)
        self.checkout()
        self.p1.price = 99999
        self.p1.save()
        self.assertEqual(OrderItem.objects.get().unit_price, 10000)

    def test_last_unit_marks_product_unavailable(self):
        self.add(self.p2, 5)
        self.checkout()
        self.p2.refresh_from_db()
        self.assertEqual(self.p2.stock, 0)
        self.assertFalse(self.p2.is_available)

    def test_cannot_add_more_than_stock_to_cart(self):
        self.add(self.p2, 7)  # omborda 5 ta
        self.assertEqual(self.client.session["cart"][str(self.p2.id)], 5)

    def test_checkout_rolls_back_when_stock_changed_meanwhile(self):
        self.add(self.p1, 2)
        self.add(self.p2, 1)
        self.p2.stock = 0
        self.p2.save()
        response = self.checkout()
        self.assertRedirects(response, reverse("cart"))
        self.assertEqual(Order.objects.count(), 0)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock, 10)  # birinchi mahsulot ham ayrilmagan

    def test_empty_cart_checkout_redirects(self):
        self.assertRedirects(self.client.get(reverse("checkout")), reverse("cart"))


@PLAIN_STATIC
class OrderAccessTests(TestCase):
    def setUp(self):
        region = Region.objects.create(name="Toshkent", delivery_cost=15000)
        self.order = Order.objects.create(
            full_name="Mijoz A", phone_number="+998900000000", region=region, address="Manzil",
            product_total=10000, delivery_fee=15000, total_amount=25000)

    def test_order_opens_by_token(self):
        response = self.client.get(reverse("order_success", args=[self.order.token]))
        self.assertContains(response, "Mijoz A")

    def test_order_cannot_be_guessed_by_sequential_id(self):
        self.assertEqual(self.client.get(f"/buyurtma/{self.order.id}/").status_code, 404)

    def test_tokens_are_unique(self):
        other = Order.objects.create(full_name="B", phone_number="1", address="x",
                                     product_total=1, delivery_fee=1, total_amount=2)
        self.assertNotEqual(self.order.token, other.token)

    def test_my_orders_requires_login_and_shows_only_own(self):
        self.assertEqual(self.client.get(reverse("my_orders")).status_code, 302)
        user = make_user()
        Order.objects.create(user=user, full_name="Mening", phone_number="1", address="x",
                             product_total=1, delivery_fee=1, total_amount=2)
        self.client.login(username="user@example.com", password="pass12345")
        response = self.client.get(reverse("my_orders"))
        self.assertContains(response, "Mening")
        self.assertNotContains(response, "Mijoz A")


@PLAIN_STATIC
class AuthTests(TestCase):
    def test_register_logs_user_in(self):
        response = self.client.post(reverse("register"), {
            "full_name": "Test", "email": "Test@Example.com", "phone_number": "+998901112233",
            "password1": "testpass123", "password2": "testpass123"})
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(CustomUser.objects.get().email, "test@example.com")

    def test_register_rejects_mismatched_passwords(self):
        self.client.post(reverse("register"), {
            "full_name": "Test", "email": "t@e.com", "phone_number": "1",
            "password1": "testpass123", "password2": "boshqa12345"})
        self.assertEqual(CustomUser.objects.count(), 0)

    def test_login_with_email_and_open_redirect_blocked(self):
        make_user()
        response = self.client.post(reverse("login"), {
            "username": "user@example.com", "password": "pass12345", "next": "https://evil.example.com/"})
        self.assertRedirects(response, reverse("home"))

    def test_logout_requires_post(self):
        make_user()
        self.client.login(username="user@example.com", password="pass12345")
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)


@PLAIN_STATIC
class ReviewTests(TestCase):
    def setUp(self):
        self.product = make_product()
        self.user = make_user()
        self.url = reverse("product_detail", args=[self.product.slug])

    def test_product_page_renders(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_user_can_review_and_rating_is_averaged(self):
        self.client.login(username="user@example.com", password="pass12345")
        self.client.post(self.url, {"submit_review": "1", "rating": 4, "text": "Yaxshi"})
        other = make_user("b@example.com")
        self.client.login(username="b@example.com", password="pass12345")
        self.client.post(self.url, {"submit_review": "1", "rating": 5, "text": "A'lo"})
        self.assertEqual(self.product.average_rating, 4.5)
        self.assertEqual(self.product.reviews_count, 2)

    def test_anonymous_cannot_review(self):
        self.client.post(self.url, {"submit_review": "1", "rating": 5})
        self.assertEqual(Review.objects.count(), 0)

    def test_second_review_updates_instead_of_duplicating(self):
        self.client.login(username="user@example.com", password="pass12345")
        self.client.post(self.url, {"submit_review": "1", "rating": 3})
        self.client.post(self.url, {"submit_review": "1", "rating": 5})
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.get().rating, 5)

    def test_invalid_rating_rejected(self):
        self.client.login(username="user@example.com", password="pass12345")
        self.client.post(self.url, {"submit_review": "1", "rating": 9})
        self.assertEqual(Review.objects.count(), 0)


@PLAIN_STATIC
class FavoriteTests(TestCase):
    def setUp(self):
        self.product = make_product()
        self.user = make_user()
        self.url = reverse("favorite_toggle", args=[self.product.id])

    def test_toggle_adds_then_removes(self):
        self.client.login(username="user@example.com", password="pass12345")
        self.client.post(self.url)
        self.assertTrue(Favorite.objects.filter(user=self.user, product=self.product).exists())
        self.client.post(self.url)
        self.assertFalse(Favorite.objects.exists())

    def test_requires_login_and_post(self):
        self.assertEqual(self.client.post(self.url).status_code, 302)
        self.client.login(username="user@example.com", password="pass12345")
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_favorites_page_lists_only_own(self):
        self.client.login(username="user@example.com", password="pass12345")
        self.client.post(self.url)
        self.assertContains(self.client.get(reverse("favorites")), self.product.title)


@PLAIN_STATIC
class PagesSmokeTests(TestCase):
    def test_public_pages_render(self):
        make_product()
        for name in ["home", "catalog", "cart", "login", "register"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertEqual(self.client.get(reverse("search"), {"q": "Pomi"}).status_code, 200)
