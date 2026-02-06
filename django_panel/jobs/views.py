"""
API Views
"""
import json
import time
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.shortcuts import render
from django.http import StreamingHttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import CrawlJob, CrawlRecord
from .serializers import (
    CrawlJobSerializer, CrawlJobCreateSerializer,
    CrawlRecordSerializer, CrawlJobStatsSerializer
)
from .tasks import run_crawl_job, fetch_mojavez_details_for_job


@login_required
@user_passes_test(lambda u: u.is_staff)
def index_view(request):
    """صفحه اصلی پنل - فقط برای کاربران ادمین (is_staff) قابل دسترسی است"""
    return render(request, 'jobs/index.html')


def events_view(request):
    """Server-Sent Events endpoint for real-time updates"""
    import json
    import time
    from django.http import StreamingHttpResponse
    
    def event_stream():
        last_stats = None
        last_jobs = {}
        
        while True:
            try:
                # Get current stats
                stats = {
                    'total_jobs': CrawlJob.objects.count(),
                    'pending_jobs': CrawlJob.objects.filter(status='pending').count(),
                    'running_jobs': CrawlJob.objects.filter(status='running').count(),
                    'completed_jobs': CrawlJob.objects.filter(status='completed').count(),
                    'failed_jobs': CrawlJob.objects.filter(status='failed').count(),
                    'total_records': CrawlRecord.objects.count(),
                }
                
                # Get running jobs
                running_jobs = CrawlJob.objects.filter(status='running').values(
                    'id', 'progress_percentage', 'fetched_records', 
                    'total_records', 'current_page', 'total_pages'
                )
                
                # Check if stats changed
                stats_changed = stats != last_stats
                
                # Check if any job progress changed
                jobs_changed = False
                current_jobs = {job['id']: job for job in running_jobs}
                
                if current_jobs != last_jobs:
                    jobs_changed = True
                    last_jobs = current_jobs
                
                # Send stats update
                if stats_changed:
                    yield f"data: {json.dumps({'type': 'stats', 'data': stats})}\n\n"
                    last_stats = stats
                
                # Send job updates
                if jobs_changed:
                    for job in running_jobs:
                        yield f"data: {json.dumps({'type': 'job_update', 'data': job})}\n\n"
                
                # Keep connection alive
                yield f": heartbeat\n\n"
                
                time.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break
    
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
    return response


@method_decorator(csrf_exempt, name='dispatch')
class CrawlJobViewSet(viewsets.ModelViewSet):
    """ViewSet برای مدیریت کراول جاب‌ها"""
    queryset = CrawlJob.objects.all()
    serializer_class = CrawlJobSerializer
    pagination_class = None  # Disable pagination for jobs list
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CrawlJobCreateSerializer
        return CrawlJobSerializer
    
    def create(self, request, *args, **kwargs):
        """ایجاد کراول جاب جدید و شروع آن"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        job = serializer.save()
        
        # شروع کراول در پس‌زمینه
        task = run_crawl_job.delay(job.id)
        job.task_id = task.id
        job.save()
        
        response_serializer = CrawlJobSerializer(job)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """شروع یک کراول جاب"""
        job = self.get_object()
        
        if job.status == 'running':
            return Response(
                {'error': 'Job is already running'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if job.status == 'completed':
            return Response(
                {'error': 'Job is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # شروع کراول
        task = run_crawl_job.delay(job.id)
        job.task_id = task.id
        job.save()
        
        return Response({'message': 'Job started', 'task_id': task.id})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """لغو یک کراول جاب"""
        job = self.get_object()
        
        if job.status != 'running':
            return Response(
                {'error': 'Job is not running'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # لغو task در Celery
        from celery import current_app
        if job.task_id:
            current_app.control.revoke(job.task_id, terminate=True)
        
        job.status = 'cancelled'
        job.save()
        
        return Response({'message': 'Job cancelled'})
    
    @action(detail=True, methods=['get'])
    def records(self, request, pk=None):
        """دریافت رکوردهای یک کراول جاب"""
        job = self.get_object()
        records = job.records.all()
        
        page = self.paginate_queryset(records)
        if page is not None:
            serializer = CrawlRecordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CrawlRecordSerializer(records, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """دریافت آمار کلی"""
        stats = {
            'total_jobs': CrawlJob.objects.count(),
            'pending_jobs': CrawlJob.objects.filter(status='pending').count(),
            'running_jobs': CrawlJob.objects.filter(status='running').count(),
            'completed_jobs': CrawlJob.objects.filter(status='completed').count(),
            'failed_jobs': CrawlJob.objects.filter(status='failed').count(),
            'total_records': CrawlRecord.objects.count(),
        }
        
        serializer = CrawlJobStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def fetch_details(self, request, pk=None):
        """
        راه‌اندازی تسک Celery برای کشیدن جزئیات صفحه track (mojavez_detail)
        """
        job = self.get_object()
        task = fetch_mojavez_details_for_job.delay(job.id)
        return Response(
            {"message": "Detail fetch started", "task_id": task.id},
            status=status.HTTP_202_ACCEPTED,
        )


class CrawlRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet برای مشاهده رکوردهای کراول"""
    queryset = CrawlRecord.objects.all()
    serializer_class = CrawlRecordSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        job_id = self.request.query_params.get('job_id', None)
        
        if job_id:
            queryset = queryset.filter(crawl_job_id=job_id)
        
        return queryset
