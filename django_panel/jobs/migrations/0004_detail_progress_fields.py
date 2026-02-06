from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0003_mojavez_detail"),
    ]

    operations = [
        migrations.AddField(
            model_name="crawljob",
            name="detail_total",
            field=models.IntegerField(
                default=0, verbose_name="تعداد کل رکوردهای جزئیات"
            ),
        ),
        migrations.AddField(
            model_name="crawljob",
            name="detail_processed",
            field=models.IntegerField(
                default=0, verbose_name="تعداد جزئیات پردازش‌شده"
            ),
        ),
        migrations.AddField(
            model_name="crawljob",
            name="detail_errors",
            field=models.IntegerField(
                default=0, verbose_name="تعداد خطا در جزئیات"
            ),
        ),
        migrations.AddField(
            model_name="crawljob",
            name="detail_status",
            field=models.CharField(
                max_length=20,
                null=True,
                blank=True,
                verbose_name="وضعیت دریافت جزئیات",
                help_text="pending / running / completed / failed",
            ),
        ),
    ]

