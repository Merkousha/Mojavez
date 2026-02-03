"""
Serializers for API
"""
from rest_framework import serializers
from .models import CrawlJob, CrawlRecord


class CrawlRecordSerializer(serializers.ModelSerializer):
    """Serializer برای رکوردهای کراول"""
    
    class Meta:
        model = CrawlRecord
        fields = [
            'id', 'request_number', 'applicant_name', 'license_title',
            'organization_title', 'province_title', 'township_title',
            'responded_at', 'status_title', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CrawlJobSerializer(serializers.ModelSerializer):
    """Serializer برای کراول جاب"""
    records_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CrawlJob
        fields = [
            'id', 'name', 'start_date', 'end_date',
            'province_id', 'township_id', 'province_name', 'township_name',
            'status', 'total_records', 'fetched_records',
            'current_page', 'total_pages', 'progress_percentage',
            'created_at', 'started_at', 'completed_at',
            'error_message', 'task_id', 'records_count'
        ]
        read_only_fields = [
            'id', 'status', 'total_records', 'fetched_records',
            'current_page', 'total_pages', 'progress_percentage',
            'created_at', 'started_at', 'completed_at',
            'error_message', 'task_id'
        ]
    
    def get_records_count(self, obj):
        """تعداد رکوردهای این جاب"""
        return obj.records.count()


class CrawlJobCreateSerializer(serializers.ModelSerializer):
    """Serializer برای ایجاد کراول جاب"""
    
    class Meta:
        model = CrawlJob
        fields = [
            'name', 'start_date', 'end_date',
            'province_id', 'township_id', 'province_name', 'township_name'
        ]


class CrawlJobStatsSerializer(serializers.Serializer):
    """Serializer برای آمار"""
    total_jobs = serializers.IntegerField()
    pending_jobs = serializers.IntegerField()
    running_jobs = serializers.IntegerField()
    completed_jobs = serializers.IntegerField()
    failed_jobs = serializers.IntegerField()
    total_records = serializers.IntegerField()
