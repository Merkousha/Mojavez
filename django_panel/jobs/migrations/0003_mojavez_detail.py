from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0002_add_location_ids"),
    ]

    operations = [
        migrations.CreateModel(
            name="MojavezDetail",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "request_number",
                    models.CharField(
                        max_length=100,
                        db_index=True,
                        verbose_name="شماره درخواست",
                    ),
                ),
                (
                    "license_title",
                    models.CharField(
                        max_length=500,
                        null=True,
                        blank=True,
                        verbose_name="عنوان مجوز",
                    ),
                ),
                (
                    "organization_title",
                    models.CharField(
                        max_length=500,
                        null=True,
                        blank=True,
                        verbose_name="مرجع صدور",
                    ),
                ),
                (
                    "isic_code",
                    models.CharField(
                        max_length=100,
                        null=True,
                        blank=True,
                        verbose_name="کد آیسیک",
                    ),
                ),
                (
                    "issue_type",
                    models.CharField(
                        max_length=200,
                        null=True,
                        blank=True,
                        verbose_name="نوع صدور",
                    ),
                ),
                (
                    "issued_at",
                    models.CharField(
                        max_length=50,
                        null=True,
                        blank=True,
                        verbose_name="تاریخ صدور / تمدید",
                    ),
                ),
                (
                    "expires_at",
                    models.CharField(
                        max_length=50,
                        null=True,
                        blank=True,
                        verbose_name="تاریخ اعتبار",
                    ),
                ),
                (
                    "province_title",
                    models.CharField(
                        max_length=100,
                        null=True,
                        blank=True,
                        verbose_name="استان (جزئیات)",
                    ),
                ),
                (
                    "township_title",
                    models.CharField(
                        max_length=100,
                        null=True,
                        blank=True,
                        verbose_name="شهرستان (جزئیات)",
                    ),
                ),
                (
                    "postal_code",
                    models.CharField(
                        max_length=50,
                        null=True,
                        blank=True,
                        verbose_name="کدپستی",
                    ),
                ),
                (
                    "business_address",
                    models.TextField(
                        null=True,
                        blank=True,
                        verbose_name="نشانی کسب و کار",
                    ),
                ),
                (
                    "status_title",
                    models.CharField(
                        max_length=100,
                        null=True,
                        blank=True,
                        verbose_name="وضعیت مجوز",
                    ),
                ),
                (
                    "status_slug",
                    models.CharField(
                        max_length=100,
                        null=True,
                        blank=True,
                        verbose_name="Slug وضعیت مجوز",
                    ),
                ),
                (
                    "raw_data",
                    models.JSONField(
                        null=True,
                        blank=True,
                        verbose_name="داده خام (JSON)",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="تاریخ ایجاد"
                    ),
                ),
                (
                    "crawl_record",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="detail",
                        to="jobs.crawlrecord",
                        verbose_name="رکورد کراول",
                    ),
                ),
            ],
            options={
                "verbose_name": "جزئیات مجوز",
                "verbose_name_plural": "جزئیات مجوزها",
                "db_table": "mojavez_detail",
            },
        ),
        migrations.AddIndex(
            model_name="mojavezdetail",
            index=models.Index(
                fields=["request_number"], name="mojavez_det_request_ef3ccd_idx"
            ),
        ),
    ]

