from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("katalog/", views.catalog, name="catalog"),
    path("katalog/<slug:category_slug>/", views.catalog, name="catalog_by_category"),
    path("mahsulot/<slug:slug>/", views.product_detail, name="product_detail"),
    path("qidiruv/", views.search, name="search"),
    path("savat/", views.cart_view, name="cart"),
    path("savat/qoshish/<int:product_id>/", views.cart_add, name="cart_add"),
    path("savat/kop/<int:product_id>/", views.cart_increase, name="cart_increase"),
    path("savat/kam/<int:product_id>/", views.cart_decrease, name="cart_decrease"),
    path("savat/ochirish/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path('checkout/<int:product_id>/', views.checkout, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
]
