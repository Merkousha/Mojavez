from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="crawlrecord",
            name="province_id",
            field=models.IntegerField(
                null=True,
                blank=True,
                verbose_name="شناسه استان",
            ),
        ),
        migrations.AddField(
            model_name="crawlrecord",
            name="township_id",
            field=models.IntegerField(
                null=True,
                blank=True,
                verbose_name="شناسه شهر",
            ),
        ),
    ]

