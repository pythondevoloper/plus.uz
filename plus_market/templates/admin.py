from django.contrib import admin
from .models import Category, Product

admin.site.site_header = "Plus Market — boshqaruv paneli"
admin.site.site_title = "Plus Market Admin"
admin.site.index_title = "Boshqaruv paneliga xush kelibsiz"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "old_price", "discount_percent", "in_stock", "created_at")
    list_filter = ("category", "in_stock")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
