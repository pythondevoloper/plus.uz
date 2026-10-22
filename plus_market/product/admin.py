from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import CustomUser, Region, Category, Product, Order, OrderItem, Review, Favorite


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
    list_display = ('id', 'title', 'category', 'formatted_price', 'stock_display',
                    'rating_display', 'is_available', 'created_at')
    list_filter = ('category', 'unit', 'is_available')
    search_fields = ('title', 'description')
    list_editable = ('is_available',)
    prepopulated_fields = {'slug': ('title',)}

    @admin.display(description="Narxi")
    def formatted_price(self, obj):
        return f"{obj.price:,.0f} so'm / {obj.unit}".replace(",", " ")

    @admin.display(description="Mavjud zaxira")
    def stock_display(self, obj):
        return f"{obj.stock} {obj.unit}"

    @admin.display(description="Reyting")
    def rating_display(self, obj):
        return f"{obj.average_rating} ★ ({obj.reviews_count})" if obj.reviews_count else "—"


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_title', 'unit_price', 'quantity')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('id', 'full_name', 'phone_number', 'region', 'formatted_total', 'status', 'created_at')
    list_filter = ('status', 'region', 'created_at')
    search_fields = ('full_name', 'phone_number', 'address', 'token')
    list_editable = ('status',)
    readonly_fields = ('token',)
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Jami summa (yetkazib berish bilan)")
    def formatted_total(self, obj):
        return f"{obj.total_amount:,.0f} so'm".replace(",", " ")


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__title', 'user__email', 'text')


@admin.register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    search_fields = ('user__email', 'product__title')
