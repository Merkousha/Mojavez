"""
Django Admin configuration
"""
from django.contrib import admin
from .models import CrawlJob, CrawlRecord


@admin.register(CrawlJob)
class CrawlJobAdmin(admin.ModelAdmin):
    """Admin برای کراول جاب"""
    list_display = [
        'id', 'name', 'status', 'total_records', 'fetched_records',
        'progress_percentage', 'created_at', 'started_at', 'completed_at'
    ]
    list_filter = ['status', 'created_at', 'started_at']
    search_fields = ['name', 'province_name', 'township_name']
    readonly_fields = [
        'created_at', 'started_at', 'completed_at',
        'total_records', 'fetched_records', 'progress_percentage',
        'current_page', 'total_pages', 'task_id'
    ]
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'start_date', 'end_date', 'status')
        }),
        ('موقعیت', {
            'fields': ('province_id', 'province_name', 'township_id', 'township_name')
        }),
        ('پیشرفت', {
            'fields': (
                'total_records', 'fetched_records', 'progress_percentage',
                'current_page', 'total_pages'
            )
        }),
        ('زمان‌بندی', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
        ('سایر', {
            'fields': ('task_id', 'error_message')
        }),
    )


@admin.register(CrawlRecord)
class CrawlRecordAdmin(admin.ModelAdmin):
    """Admin برای رکوردهای کراول"""
    list_display = [
        'id', 'request_number', 'applicant_name', 'license_title',
        'province_title', 'township_title', 'status_title', 'created_at'
    ]
    list_filter = ['crawl_job', 'status_title', 'province_title', 'created_at']
    search_fields = [
        'request_number', 'applicant_name', 'license_title',
        'organization_title', 'province_title', 'township_title'
    ]
    readonly_fields = ['created_at', 'raw_data']
    raw_id_fields = ['crawl_job']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('crawl_job', 'request_number', 'applicant_name')
        }),
        ('اطلاعات مجوز', {
            'fields': ('license_title', 'organization_title')
        }),
        ('موقعیت', {
            'fields': ('province_title', 'township_title')
        }),
        ('وضعیت', {
            'fields': ('status_id', 'status_title', 'status_slug', 'responded_at')
        }),
        ('سایر', {
            'fields': ('user_image', 'created_at', 'raw_data')
        }),
    )
