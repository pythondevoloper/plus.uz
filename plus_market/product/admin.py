from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import CustomUser, Region, Category, Product, Order

@admin.register(CustomUser)
class CustomUserAdmin(ModelAdmin):
    list_display = ('email', 'full_name', 'phone_number', 'is_staff', 'is_active')
    search_fields = ('email', 'full_name', 'phone_number')

@admin.register(Region)
class RegionAdmin(ModelAdmin):
    list_display = ('name', 'formatted_delivery_cost')

    @admin.display(description="Yetkazib berish narxi")
    def formatted_delivery_cost(self, obj):
        return f"{obj.delivery_cost:,.0f} so'm".replace(",", " ")

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('id', 'name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('id', 'title', 'category', 'formatted_price', 'stock_display', 'is_available', 'created_at')
    list_filter = ('category', 'unit', 'is_available')
    search_fields = ('title', 'description')
    list_editable = ('is_available',)
    prepopulated_fields = {'slug': ('title',)}

    @admin.display(description="Narxi")
    def formatted_price(self, obj):
        return f"{obj.price:,.0f} so'm / {obj.unit}".replace(",", " ")

    @admin.display(description="Mavjud Zaxira")
    def stock_display(self, obj):
        return f"{obj.stock} {obj.unit}"

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('id', 'full_name', 'phone_number', 'region', 'formatted_total', 'status', 'created_at')
    list_filter = ('status', 'region', 'created_at')
    search_fields = ('full_name', 'phone_number', 'address')
    list_editable = ('status',)

    # Adminlar buyurtma qo'sholmaydi va o'chira olmaydi (faqat ko'radi va holatni o'zgartiradi)
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Jami Summa (Yetkazib berish bilan)")
    def formatted_total(self, obj):
        return f"{obj.total_amount:,.0f} so'm".replace(",", " ")