# Plus Market (plus.uz)

Django 4.2 asosidagi onlayn market: katalog, savat, buyurtma, shaxsiy kabinet, sharhlar va sevimlilar.
Admin panel `django-unfold` bilan.

## Imkoniyatlar

- **Katalog va qidiruv** — kategoriyalar, mahsulot sahifasi (`/mahsulot/<slug>/`)
- **Savat** — sessiyada saqlanadi; barcha o'zgartirishlar faqat `POST` (CSRF himoyasi bilan); ombordagi miqdordan ortig'ini qo'shib bo'lmaydi
- **Checkout** — savatdagi **barcha** mahsulotlar `OrderItem` sifatida saqlanadi; narx va nom buyurtma vaqtida "suratga olinadi"
- **Ombor himoyasi** — buyurtma `transaction.atomic()` + `select_for_update()` ichida yaratiladi: xatolik bo'lsa hech narsa saqlanmaydi, PostgreSQL/MySQL'da parallel buyurtmalar bir xil zaxirani ikki marta sota olmaydi
- **Buyurtma maxfiyligi** — buyurtma sahifasi ketma-ket ID bilan emas, taxmin qilib bo'lmaydigan UUID `token` bilan ochiladi (`/buyurtma/<uuid>/`)
- **Ro'yxatdan o'tish / kirish (email orqali) / shaxsiy kabinet** — profilni tahrirlash, buyurtmalar tarixi
- **Sharh va reyting** — 1–5 yulduz; bitta foydalanuvchi bitta mahsulotga bitta sharh (qayta yuborsa yangilanadi)
- **Sevimlilar ro'yxati**

## Ishga tushirish

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r plus_market/requirements.txt

cd plus_market
cp .env.example .env               # Windows: copy .env.example .env  — so'ng qiymatlarni to'ldiring
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Sayt: http://127.0.0.1:8000/ · Admin: http://127.0.0.1:8000/admin/

> Mavjud `db.sqlite3` bilan ishlayotgan bo'lsangiz ham faqat `python manage.py migrate` yetarli:
> `0002` migratsiyasi eski buyurtmalarning har biriga alohida `token` beradi.

## Sozlamalar (`.env`)

| O'zgaruvchi | Tavsif | Standart |
|---|---|---|
| `SECRET_KEY` | Django maxfiy kaliti. **Productionda majburiy** — bo'lmasa loyiha ishga tushmaydi | — |
| `DEBUG` | `True` faqat lokal rivojlantirishda | `False` |
| `ALLOWED_HOSTS` | Vergul bilan ajratilgan domenlar | `127.0.0.1,localhost` |

Kalit yaratish:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Production uchun

```bash
DEBUG=False SECRET_KEY=... ALLOWED_HOSTS=plus.uz python manage.py collectstatic --noinput
gunicorn plus_market.wsgi
```
Parallel buyurtmalardan to'liq himoya uchun SQLite o'rniga **PostgreSQL** tavsiya etiladi
(SQLite `select_for_update()` qulfini e'tiborsiz qoldiradi).

## Testlar

```bash
cd plus_market
python manage.py test product
```
25 ta test: ko'p mahsulotli checkout, ombor kamayishi va rollback, narx "snapshot"i, savat amallarining faqat POST ekani,
buyurtma token orqali ochilishi (ID orqali 404), faqat o'z buyurtmalarini ko'rish, ro'yxatdan o'tish/kirish,
open-redirect himoyasi, sharh va sevimlilar.

## Loyiha tuzilishi

```
plus_market/
├── plus_market/      # settings, urls, wsgi
├── product/          # models, views, forms, admin, tests, migrations, static
└── templates/        # base, home, catalog, product_detail, cart, checkout,
                      # order_success, my_orders, profile, favorites, login, register
```

## Keyingi rejalar

Promo-kod va chegirmalar, buyurtma holati o'zgarganda Telegram xabarnomasi, admin uchun sotuvlar hisoboti.
