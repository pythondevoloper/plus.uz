from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Product, Category, Region, Order, OrderItem, Favorite
from .forms import RegisterForm, EmailAuthenticationForm, ProfileForm, ReviewForm


# ---------------------------------------------------------------
# Yordamchilar. Savat sessiyada {"<product_id>": quantity} ko'rinishida saqlanadi.
# ---------------------------------------------------------------

def _get_cart(request):
    return request.session.get("cart", {})


def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def _build_cart_items(cart):
    items, total = [], 0
    if not cart:
        return items, total
    products = {p.id: p for p in Product.objects.filter(id__in=[int(pid) for pid in cart])}
    for pid, qty in cart.items():
        product = products.get(int(pid))
        if not product:
            continue
        qty = int(qty)
        item_total = product.price * qty
        total += item_total
        items.append({"product": product, "quantity": qty, "total": item_total})
    return items, total


def _safe_next(request, fallback):
    """Open-redirect'dan himoya: faqat shu saytning ichki manzillariga ruxsat."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return fallback


# ---------------------------------------------------------------
# Katalog
# ---------------------------------------------------------------

def home(request):
    return render(request, "home.html", {
        "products": Product.objects.filter(is_available=True)[:8],
        "categories": Category.objects.all(),
    })


def catalog(request, category_slug=None):
    category = None
    products = Product.objects.filter(is_available=True)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request, "catalog.html", {
        "category": category, "categories": Category.objects.all(), "products": products,
    })


def search(request):
    query = request.GET.get("q", "").strip()
    products = Product.objects.filter(is_available=True)
    if query:
        products = products.filter(Q(title__icontains=query) | Q(description__icontains=query))
    return render(request, "catalog.html", {"products": products, "query": query})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    reviews = product.reviews.select_related("user")

    user_review, is_favorite = None, False
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
        is_favorite = Favorite.objects.filter(user=request.user, product=product).exists()

    review_form = ReviewForm(instance=user_review)

    if request.method == "POST" and "submit_review" in request.POST:
        if not request.user.is_authenticated:
            messages.error(request, "Sharh qoldirish uchun avval tizimga kiring.")
            return redirect("login")
        review_form = ReviewForm(request.POST, instance=user_review)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Sharhingiz uchun rahmat!")
            return redirect("product_detail", slug=product.slug)

    related = Product.objects.filter(category=product.category, is_available=True).exclude(id=product.id)[:4]
    return render(request, "product_detail.html", {
        "product": product, "reviews": reviews, "review_form": review_form,
        "user_review": user_review, "is_favorite": is_favorite, "related_products": related,
    })


# ---------------------------------------------------------------
# Savat — o'zgartiruvchi amallar faqat POST (GET orqali CSRF/prefetch xavfi bor edi)
# ---------------------------------------------------------------

def cart_view(request):
    items, total = _build_cart_items(_get_cart(request))
    return render(request, "cart.html", {"cart_items": items, "total_price": total})


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    cart = _get_cart(request)
    key = str(product_id)
    if cart.get(key, 0) + 1 > product.stock:
        messages.error(request, f"Omborda faqat {product.stock} ta '{product.title}' bor.")
    else:
        cart[key] = cart.get(key, 0) + 1
        _save_cart(request, cart)
    return redirect(_safe_next(request, "cart"))


@require_POST
def cart_increase(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = _get_cart(request)
    key = str(product_id)
    if key in cart:
        if cart[key] + 1 > product.stock:
            messages.error(request, f"Omborda faqat {product.stock} ta '{product.title}' bor.")
        else:
            cart[key] += 1
            _save_cart(request, cart)
    return redirect("cart")


@require_POST
def cart_decrease(request, product_id):
    cart = _get_cart(request)
    key = str(product_id)
    if key in cart:
        if cart[key] > 1:
            cart[key] -= 1
        else:
            del cart[key]
        _save_cart(request, cart)
    return redirect("cart")


@require_POST
def cart_remove(request, product_id):
    cart = _get_cart(request)
    if cart.pop(str(product_id), None) is not None:
        _save_cart(request, cart)
    return redirect("cart")


# ---------------------------------------------------------------
# Checkout — savatdagi BARCHA mahsulotlar, bitta tranzaksiyada
# ---------------------------------------------------------------

def checkout(request):
    cart = _get_cart(request)
    if not cart:
        messages.info(request, "Savatingiz bo'sh.")
        return redirect("cart")

    cart_items, product_total = _build_cart_items(cart)
    regions = Region.objects.all()
    ctx = {"cart_items": cart_items, "product_total": product_total, "regions": regions}

    if request.method != "POST":
        return render(request, "checkout.html", ctx)

    full_name = request.POST.get("full_name", "").strip()
    phone_number = request.POST.get("phone_number", "").strip()
    region_id = request.POST.get("region")
    address = request.POST.get("address", "").strip()
    if not (full_name and phone_number and region_id and address):
        messages.error(request, "Barcha maydonlarni to'ldiring.")
        return render(request, "checkout.html", ctx)

    region = get_object_or_404(Region, id=region_id)

    # Qatorlarni qulflab (PostgreSQL/MySQL'da select_for_update haqiqiy qulf beradi), omborni tekshirib,
    # keyin ayiramiz. Parallel ikki buyurtma bir xil zaxirani "ikki marta" sota olmaydi.
    # SQLite qulfni e'tiborsiz qoldiradi, lekin atomiklik (hammasi yoki hech narsa) baribir ta'minlanadi.
    with transaction.atomic():
        locked = {p.id: p for p in Product.objects.select_for_update().filter(id__in=[int(i) for i in cart])}

        errors = []
        for pid, qty in cart.items():
            product = locked.get(int(pid))
            if not product or not product.is_available:
                errors.append("Savatdagi mahsulotlardan biri endi mavjud emas.")
            elif int(qty) > product.stock:
                errors.append(f"'{product.title}': omborda faqat {product.stock} ta qoldi.")
        if errors:
            for e in errors:
                messages.error(request, e)
            return redirect("cart")

        # Narxlarni QULFLANGAN (eng so'nggi) ma'lumotdan qayta hisoblaymiz
        product_total = sum(locked[int(pid)].price * int(qty) for pid, qty in cart.items())
        delivery_fee = region.delivery_cost

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name, phone_number=phone_number, region=region, address=address,
            product_total=product_total, delivery_fee=delivery_fee,
            total_amount=product_total + delivery_fee, status="pending",
        )
        for pid, qty in cart.items():
            product, qty = locked[int(pid)], int(qty)
            OrderItem.objects.create(order=order, product=product, product_title=product.title,
                                     unit_price=product.price, quantity=qty)
            product.stock -= qty
            if product.stock <= 0:
                product.is_available = False
            product.save(update_fields=["stock", "is_available"])

    _save_cart(request, {})
    return redirect("order_success", token=order.token)


def order_success(request, token):
    # ID emas, taxmin qilib bo'lmaydigan UUID token orqali
    order = get_object_or_404(Order.objects.prefetch_related("items"), token=token)
    return render(request, "order_success.html", {"order": order})


# ---------------------------------------------------------------
# Kabinet, autentifikatsiya, sevimlilar
# ---------------------------------------------------------------

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items").order_by("-id")
    return render(request, "my_orders.html", {"orders": orders})


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Ma'lumotlaringiz yangilandi.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)
    orders = Order.objects.filter(user=request.user).order_by("-id")[:5]
    return render(request, "profile.html", {"form": form, "orders": orders})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Xush kelibsiz! Ro'yxatdan muvaffaqiyatli o'tdingiz.")
        return redirect("home")
    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(_safe_next(request, "home"))
    return render(request, "login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Tizimdan chiqdingiz.")
    return redirect("home")


@login_required
def favorites_view(request):
    favs = Favorite.objects.filter(user=request.user).select_related("product")
    return render(request, "favorites.html", {"favorites": favs})


@require_POST
@login_required
def favorite_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    fav, created = Favorite.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, f"'{product.title}' sevimlilarga qo'shildi.")
    else:
        fav.delete()
        messages.info(request, f"'{product.title}' sevimlilardan olib tashlandi.")
    return redirect(_safe_next(request, reverse_product(product)))


def reverse_product(product):
    from django.urls import reverse
    return reverse("product_detail", args=[product.slug])
