from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import Product, Category, Region, Order

# 1. Bosh sahifa
# product/views.py

# 1. Bosh sahifa
def home(request):
    products = Product.objects.filter(is_available=True)[:8]
    categories = Category.objects.all()
    # 'index.html' o'rniga 'home.html' deb yoziladi:
    return render(request, 'home.html', {'products': products, 'categories': categories})

# 2. Katalog va Kategoriya bo'yicha saralash
def catalog(request, category_slug=None):
    category = None
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(request, 'catalog.html', {
        'category': category,
        'categories': categories,
        'products': products
    })

# 3. Mahsulot tafsilotlari
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'product_detail.html', {'product': product})

# 4. Qidiruv
def search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(is_available=True)
    if query:
        products = products.filter(Q(title__icontains=query) | Q(description__icontains=query))
    return render(request, 'catalog.html', {'products': products, 'query': query})

def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            item_total = product.price * quantity
            total_price += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
        except Product.DoesNotExist:
            continue

    first_product_id = cart_items[0]['product'].id if cart_items else None

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'first_product_id': first_product_id
    })

# 6. Savatga qo'shish
def cart_add(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    return redirect('cart')

# 7. Savatdagi sonini ko'paytirish
def cart_increase(request, product_id):
    cart = request.session.get('cart', {})
    str_id = str(product_id)
    if str_id in cart:
        cart[str_id] += 1
        request.session['cart'] = cart
    return redirect('cart')

# 8. Savatdagi sonini kamaytirish
def cart_decrease(request, product_id):
    cart = request.session.get('cart', {})
    str_id = str(product_id)
    if str_id in cart:
        if cart[str_id] > 1:
            cart[str_id] -= 1
        else:
            del cart[str_id]
        request.session['cart'] = cart
    return redirect('cart')

# 9. Savatdan o'chirish
def cart_remove(request, product_id):
    cart = request.session.get('cart', {})
    str_id = str(product_id)
    if str_id in cart:
        del cart[str_id]
        request.session['cart'] = cart
    return redirect('cart')

# 10. Buyurtmani rasmiylashtirish va Ombordan ayrish
def checkout(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    regions = Region.objects.all()

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        region_id = request.POST.get('region')
        address = request.POST.get('address')
        quantity = int(request.POST.get('quantity', 1))

        if quantity > product.stock:
            messages.error(request, f"Xatolik! Omborda faqat {product.stock} ta mahsulot bor.")
            return redirect('checkout', product_id=product.id)

        region = get_object_or_404(Region, id=region_id)
        product_total = product.price * quantity
        delivery_fee = region.delivery_cost
        total_amount = product_total + delivery_fee

        # Order yaratish (product=product olib tashlandi)
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            phone_number=phone_number,
            region=region,
            address=address,
            product_total=product_total,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
            status='pending'
        )

        # Ombordan ayrish va tugasa nodavlat qilish
        product.stock -= quantity
        if product.stock <= 0:
            product.stock = 0
            product.is_available = False

        product.save()
        return redirect('order_success', order_id=order.id)

    return render(request, 'checkout.html', {'product': product, 'regions': regions})
# 11. Buyurtma muvaffaqiyatli yakunlandi sahifasi
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_success.html', {'order': order})

def my_orders(request):
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-id')
    else:
        orders = []

    return render(request, 'my_orders.html', {'orders': orders})