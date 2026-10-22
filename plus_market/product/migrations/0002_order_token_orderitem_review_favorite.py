# Token maydoni uch bosqichda qo'shiladi: mavjud buyurtmalarning HAR BIRIGA alohida UUID berilishi uchun.
# (Bitta AddField(unique=True) qilinsa, SQLite barcha eski qatorlarga BIR XIL qiymat beradi va xato chiqadi.)
import uuid

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


def generate_unique_tokens(apps, schema_editor):
    Order = apps.get_model('product', 'Order')
    for order in Order.objects.all():
        order.token = uuid.uuid4()
        order.save(update_fields=['token'])


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='token',
            field=models.UUIDField(editable=False, null=True, verbose_name='Maxfiy identifikator (URL uchun)'),
        ),
        migrations.RunPython(generate_unique_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='order',
            name='token',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True, verbose_name='Maxfiy identifikator (URL uchun)'),
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_title', models.CharField(max_length=200, verbose_name='Mahsulot nomi (buyurtma vaqtida)')),
                ('unit_price', models.DecimalField(decimal_places=0, max_digits=12, verbose_name='Birlik narxi (buyurtma vaqtida)')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Miqdori')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='product.order', verbose_name='Buyurtma')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_items', to='product.product', verbose_name='Mahsulot')),
            ],
            options={'verbose_name': 'Buyurtma elementi', 'verbose_name_plural': 'Buyurtma elementlari'},
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Reyting (1-5)')),
                ('text', models.TextField(blank=True, verbose_name='Sharh matni')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqti')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='product.product', verbose_name='Mahsulot')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to=settings.AUTH_USER_MODEL, verbose_name='Foydalanuvchi')),
            ],
            options={'verbose_name': 'Sharh', 'verbose_name_plural': 'Sharhlar', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_at', models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan vaqti")),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorited_by', to='product.product', verbose_name='Mahsulot')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL, verbose_name='Foydalanuvchi')),
            ],
            options={'verbose_name': 'Sevimli mahsulot', 'verbose_name_plural': 'Sevimli mahsulotlar', 'ordering': ['-added_at']},
        ),
        migrations.AddConstraint(
            model_name='review',
            constraint=models.UniqueConstraint(fields=('product', 'user'), name='unique_review_per_user_product'),
        ),
        migrations.AddConstraint(
            model_name='favorite',
            constraint=models.UniqueConstraint(fields=('user', 'product'), name='unique_favorite_per_user_product'),
        ),
    ]
