from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("katalog/", views.catalog, name="catalog"),
    path("katalog/<slug:category_slug>/", views.catalog, name="catalog_by_category"),
    path("mahsulot/<slug:slug>/", views.product_detail, name="product_detail"),
    path("qidiruv/", views.search, name="search"),

    # Savat — barcha o'zgartiruvchi amallar faqat POST
    path("savat/", views.cart_view, name="cart"),
    path("savat/qoshish/<int:product_id>/", views.cart_add, name="cart_add"),
    path("savat/kop/<int:product_id>/", views.cart_increase, name="cart_increase"),
    path("savat/kam/<int:product_id>/", views.cart_decrease, name="cart_decrease"),
    path("savat/ochirish/<int:product_id>/", views.cart_remove, name="cart_remove"),

    # Checkout butun savat bilan ishlaydi; buyurtma maxfiy UUID token orqali ochiladi (ID orqali emas)
    path("checkout/", views.checkout, name="checkout"),
    path("buyurtma/<uuid:token>/", views.order_success, name="order_success"),

    path("kabinet/", views.profile, name="profile"),
    path("buyurtmalarim/", views.my_orders, name="my_orders"),

    path("royxatdan-otish/", views.register_view, name="register"),
    path("kirish/", views.login_view, name="login"),
    path("chiqish/", views.logout_view, name="logout"),

    path("sevimlilar/", views.favorites_view, name="favorites"),
    path("sevimlilar/almashtirish/<int:product_id>/", views.favorite_toggle, name="favorite_toggle"),
]
