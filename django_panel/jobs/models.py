"""
Models for Crawl Jobs and Records
"""
from django.db import models
from django.utils import timezone


class CrawlJob(models.Model):
    """مدل کراول جاب"""
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('running', 'در حال اجرا'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='نام کراول')
    start_date = models.CharField(max_length=20, verbose_name='تاریخ شروع')
    end_date = models.CharField(max_length=20, verbose_name='تاریخ پایان')
    
    province_id = models.IntegerField(null=True, blank=True, verbose_name='شناسه استان')
    township_id = models.IntegerField(null=True, blank=True, verbose_name='شناسه شهر')
    province_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='نام استان')
    township_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='نام شهر')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')
    total_records = models.IntegerField(default=0, verbose_name='تعداد کل رکوردها')
    fetched_records = models.IntegerField(default=0, verbose_name='تعداد رکوردهای دریافت شده')
    
    # Progress tracking
    current_page = models.IntegerField(default=0, verbose_name='صفحه فعلی')
    total_pages = models.IntegerField(default=0, verbose_name='تعداد کل صفحات')
    progress_percentage = models.IntegerField(default=0, verbose_name='درصد پیشرفت')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ شروع')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تکمیل')
    
    # Error tracking
    error_message = models.TextField(null=True, blank=True, verbose_name='پیام خطا')
    
    # Celery task ID
    task_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='شناسه Task')
    
    class Meta:
        verbose_name = 'کراول جاب'
        verbose_name_plural = 'کراول جاب‌ها'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    @property
    def is_running(self):
        return self.status == 'running'
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_failed(self):
        return self.status == 'failed'


class CrawlRecord(models.Model):
    """مدل رکوردهای کراول شده"""
    
    crawl_job = models.ForeignKey(CrawlJob, on_delete=models.CASCADE, related_name='records', verbose_name='کراول جاب')
    
    # اطلاعات رکورد
    request_number = models.CharField(max_length=100, null=True, blank=True, db_index=True, verbose_name='شماره درخواست')
    applicant_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='نام متقاضی')
    user_image = models.CharField(max_length=500, null=True, blank=True, verbose_name='تصویر کاربر')
    license_title = models.CharField(max_length=500, null=True, blank=True, verbose_name='عنوان مجوز')
    organization_title = models.CharField(max_length=500, null=True, blank=True, verbose_name='عنوان سازمان')
    province_title = models.CharField(max_length=100, null=True, blank=True, verbose_name='استان')
    township_title = models.CharField(max_length=100, null=True, blank=True, verbose_name='شهر')
    responded_at = models.CharField(max_length=50, null=True, blank=True, verbose_name='تاریخ پاسخ')
    
    # Status
    status_id = models.CharField(max_length=50, null=True, blank=True, verbose_name='شناسه وضعیت')
    status_title = models.CharField(max_length=100, null=True, blank=True, verbose_name='عنوان وضعیت')
    status_slug = models.CharField(max_length=100, null=True, blank=True, verbose_name='Slug وضعیت')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    # Raw JSON data
    raw_data = models.JSONField(null=True, blank=True, verbose_name='داده خام')
    
    class Meta:
        verbose_name = 'رکورد کراول'
        verbose_name_plural = 'رکوردهای کراول'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['crawl_job', 'request_number']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.request_number or 'N/A'} - {self.applicant_name or 'N/A'}"
