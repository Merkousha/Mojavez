from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_detail_progress_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='crawljob',
            name='target_worker',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='ورکر مقصد'),
        ),
        migrations.AddField(
            model_name='crawljob',
            name='target_queue',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='صف مقصد'),
        ),
    ]
