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
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from celery import current_app
from celery.result import AsyncResult
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


def _get_workers_info():
    inspect = current_app.control.inspect()
    active_queues = inspect.active_queues() or {}
    pings = inspect.ping() or {}
    workers = []

    for worker_name, queues in active_queues.items():
        queue_names = [q.get('name') for q in (queues or []) if q.get('name')]
        workers.append({
            'name': worker_name,
            'queues': queue_names,
            'online': worker_name in pings,
        })

    for worker_name in settings.CELERY_KNOWN_WORKERS:
        if worker_name not in active_queues:
            workers.append({
                'name': worker_name,
                'queues': [settings.CELERY_DEFAULT_QUEUE],
                'online': False,
            })

    return workers


def _resolve_target_queue(target_worker=None, target_queue=None):
    if target_queue:
        return target_queue

    if target_worker:
        workers = _get_workers_info()
        for worker in workers:
            if worker.get('name') == target_worker:
                queues = worker.get('queues') or []
                if queues:
                    return queues[0]

    return settings.CELERY_DEFAULT_QUEUE


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

        target_worker = serializer.validated_data.get('target_worker')
        target_queue = serializer.validated_data.get('target_queue')
        resolved_queue = _resolve_target_queue(target_worker, target_queue)
        job.target_worker = target_worker or None
        job.target_queue = resolved_queue

        # شروع کراول در پس‌زمینه
        task = run_crawl_job.apply_async(args=[job.id], queue=resolved_queue)
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
        
        target_worker = request.data.get('target_worker') or job.target_worker
        target_queue = request.data.get('target_queue') or job.target_queue
        resolved_queue = _resolve_target_queue(target_worker, target_queue)
        job.target_worker = target_worker or job.target_worker
        job.target_queue = resolved_queue

        # شروع کراول
        task = run_crawl_job.apply_async(args=[job.id], queue=resolved_queue)
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
        target_worker = request.data.get('target_worker') or job.target_worker
        target_queue = request.data.get('target_queue') or job.target_queue
        resolved_queue = _resolve_target_queue(target_worker, target_queue)
        job.target_worker = target_worker or job.target_worker
        job.target_queue = resolved_queue
        job.save(update_fields=['target_worker', 'target_queue'])

        task = fetch_mojavez_details_for_job.apply_async(args=[job.id], queue=resolved_queue)
        return Response(
            {"message": "Detail fetch started", "task_id": task.id},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=['get'])
    def task_state(self, request, pk=None):
        """
        وضعیت تسک این job در Celery/Redis را برمی‌گرداند.
        اگر task_id نباشد یا تسک در صف/در حال اجرا نباشد، می‌توان نتیجه را «گم شده» در نظر گرفت.
        """
        job = self.get_object()
        if not job.task_id:
            return Response({
                'task_id': None,
                'state': 'no_task',
                'lost': True,
                'message': 'تسکی برای این job ثبت نشده است.',
            })
        try:
            result = AsyncResult(job.task_id, app=current_app)
            state = result.state or 'UNKNOWN'
            # PENDING = در صف یا هنوز شروع نشده؛ STARTED = در حال اجرا؛ SUCCESS/FAILURE/REVOKED = تمام شده یا لغو
            lost = state in ('PENDING', 'UNKNOWN') and job.status == 'running'
            return Response({
                'task_id': job.task_id,
                'state': state,
                'lost': lost,
                'message': _task_state_message(state, job.status),
            })
        except Exception as e:
            return Response({
                'task_id': job.task_id,
                'state': 'error',
                'lost': True,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def requeue(self, request, pk=None):
        """
        احیا: ارسال مجدد تسک این job به صف Redis (مثلاً بعد از کرش Redis و پاک شدن صف).
        تسک قبلی در صورت وجود لغو می‌شود؛ یک تسک جدید به صف فرستاده می‌شود و job از همان checkpoint ادامه می‌دهد.
        """
        job = self.get_object()
        if job.status == 'completed':
            return Response(
                {'error': 'Job is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        target_worker = request.data.get('target_worker') or job.target_worker
        target_queue = request.data.get('target_queue') or job.target_queue
        resolved_queue = _resolve_target_queue(target_worker, target_queue)
        job.target_worker = target_worker or job.target_worker
        job.target_queue = resolved_queue

        if job.task_id:
            try:
                current_app.control.revoke(job.task_id, terminate=True)
            except Exception:
                pass
            job.task_id = None

        task = run_crawl_job.apply_async(args=[job.id], queue=resolved_queue)
        job.task_id = task.id
        job.status = 'running'
        job.save(update_fields=['task_id', 'status', 'target_worker', 'target_queue'])

        return Response({
            'message': 'Job re-queued to Redis',
            'task_id': task.id,
            'queue': resolved_queue,
        })

    @action(detail=False, methods=['get'])
    def workers(self, request):
        """لیست ورکرها و صف‌های فعال"""
        workers = _get_workers_info()
        return Response({
            'workers': workers,
            'default_queue': settings.CELERY_DEFAULT_QUEUE,
        })


def _task_state_message(state: str, job_status: str) -> str:
    """پیام فارسی برای وضعیت تسک"""
    if state == 'no_task':
        return 'تسکی ثبت نشده است.'
    if state == 'PENDING':
        return 'در صف یا در انتظار شروع.'
    if state == 'STARTED':
        return 'در حال اجرا روی ورکر.'
    if state == 'SUCCESS':
        return 'با موفقیت تمام شده.'
    if state == 'FAILURE':
        return 'با خطا تمام شده.'
    if state == 'REVOKED':
        return 'لغو شده.'
    if job_status == 'running' and state in ('PENDING', 'UNKNOWN'):
        return 'احتمالاً تسک از صف رفته؛ می‌توانید «ارسال مجدد به صف» بزنید.'
    return f'وضعیت: {state}'


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
