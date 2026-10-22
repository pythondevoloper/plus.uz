import uuid
from django.db import models
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.text import slugify


# Email orqali ro'yxatdan o'tkazish uchun menejer
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email manzili kiritilishi shart!")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name="Email manzil")
    full_name = models.CharField(max_length=150, verbose_name="F.I.O")
    phone_number = models.CharField(max_length=20, verbose_name="Telefon raqami")
    address = models.TextField(verbose_name="Manzil (Ko'cha, uy binosi)", blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone_number']

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.full_name} ({self.email})"


# Viloyat va Yetkazib berish narxi
class Region(models.Model):
    name = models.CharField(max_length=100, verbose_name="Viloyat/Hudud nomi")
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Yetkazib berish narxi (so'm)")

    class Meta:
        verbose_name = "Hudud va Yetkazib berish"
        verbose_name_plural = "Hududlar va Yetkazib berish"

    def __str__(self):
        return f"{self.name} - {self.delivery_cost:,.0f} so'm".replace(",", " ")


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")
    slug = models.SlugField(unique=True, blank=True, null=True, verbose_name="URL Slug")

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_CHOICES = (
        ('dona', 'dona'),
        ('kg', 'kg'),
        ('g', 'g'),
        ('litr', 'litr'),
        ('metr', 'metr'),
        ('quti', 'quti'),
        ('pachka', 'pachka'),
    )

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", verbose_name="Kategoriya")
    title = models.CharField(max_length=200, verbose_name="Mahsulot nomi")
    slug = models.SlugField(unique=True, blank=True, null=True, verbose_name="URL Slug (Avto)")
    description = models.TextField(verbose_name="Tavsif", blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Narxi (so'mda)")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='dona', verbose_name="O'lchov birligi")

    stock = models.PositiveIntegerField(default=0, verbose_name="Mavjud miqdor (Omborda qancha bor)")
    min_order_amount = models.PositiveIntegerField(default=1, verbose_name="Eng kam xarid miqdori")

    image = models.ImageField(upload_to="products/", verbose_name="Rasm", blank=True, null=True)
    is_available = models.BooleanField(default=True, verbose_name="Mavjudligi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.price:,.0f} so'm / {self.unit}".replace(",", " ")

    @property
    def reviews_count(self):
        return self.reviews.count()

    @property
    def average_rating(self):
        avg = self.reviews.aggregate(avg=Avg("rating"))["avg"]
        return round(avg, 1) if avg else 0


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Kutilmoqda'),
        ('processing', 'Jarayonda'),
        ('completed', 'Bajarildi'),
        ('canceled', 'Bekor qilindi'),
    )

    # Maxfiy identifikator: URL'da ID o'rniga shu ishlatiladi (boshqa mijoz buyurtmasini taxmin qilib bo'lmaydi)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True,
                             verbose_name="Maxfiy identifikator (URL uchun)")
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Xaridor")
    full_name = models.CharField(max_length=150, verbose_name="F.I.O")
    phone_number = models.CharField(max_length=20, verbose_name="Telefon raqam")
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, verbose_name="Yetkazib berish hududi")
    address = models.TextField(verbose_name="Aniq manzil (Uy, ko'cha, mo'ljal)")

    product_total = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Mahsulotlar summasi")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Yetkazib berish narxi")
    total_amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Jami umumiy summa")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Buyurtma holati")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"

    def __str__(self):
        return f"Buyurtma #{self.id} - {self.full_name}"


class OrderItem(models.Model):
    """Buyurtmadagi har bir mahsulot qatori. Nom va narx buyurtma vaqtida 'suratga olinadi',
    shuning uchun mahsulot keyin o'zgartirilsa/o'chirilsa ham tarix buzilmaydi."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Buyurtma")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="order_items", verbose_name="Mahsulot")
    product_title = models.CharField(max_length=200, verbose_name="Mahsulot nomi (buyurtma vaqtida)")
    unit_price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Birlik narxi (buyurtma vaqtida)")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Miqdori")

    class Meta:
        verbose_name = "Buyurtma elementi"
        verbose_name_plural = "Buyurtma elementlari"

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.product_title} x{self.quantity}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews", verbose_name="Mahsulot")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reviews", verbose_name="Foydalanuvchi")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Reyting (1-5)")
    text = models.TextField(blank=True, verbose_name="Sharh matni")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")

    class Meta:
        verbose_name = "Sharh"
        verbose_name_plural = "Sharhlar"
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["product", "user"], name="unique_review_per_user_product")]

    def __str__(self):
        return f"{self.user} -> {self.product} ({self.rating}★)"


class Favorite(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="favorites", verbose_name="Foydalanuvchi")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="favorited_by", verbose_name="Mahsulot")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan vaqti")

    class Meta:
        verbose_name = "Sevimli mahsulot"
        verbose_name_plural = "Sevimli mahsulotlar"
        ordering = ["-added_at"]
        constraints = [models.UniqueConstraint(fields=["user", "product"], name="unique_favorite_per_user_product")]

    def __str__(self):
        return f"{self.user} ♥ {self.product.title}"
