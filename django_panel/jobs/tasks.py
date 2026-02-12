"""
Celery tasks for crawling
"""
import sys
import os
import time
import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction

# اضافه کردن مسیر اصلی پروژه
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from crawler import MojavezCrawler
from date_utils import format_date_for_api, parse_api_date
from .models import CrawlJob, CrawlRecord, MojavezDetail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=10)
def run_crawl_job(self, job_id):
    """
    Execute crawl job
    
    Args:
        job_id: Crawl job ID
    """
    try:
        logger.info(f"🚀 [Job {job_id}] Starting crawl job...")
        job = CrawlJob.objects.get(id=job_id)
        
        # Check if this is a resume (job was running before)
        is_resume = job.status == 'running' and job.fetched_records > 0
        resume_from_page = job.current_page if is_resume else 1
        existing_records_count = job.records.count() if is_resume else 0
        
        if is_resume:
            logger.info(f"🔄 [Job {job_id}] Resuming from checkpoint: {existing_records_count} records, page {resume_from_page}")
        else:
            logger.info(f"🆕 [Job {job_id}] Starting new crawl job")
        
        # Update status
        job.status = 'running'
        if not job.started_at:  # Only set if not already set (for resume)
            job.started_at = timezone.now()
        job.task_id = self.request.id
        job.save()
        logger.info(f"✅ [Job {job_id}] Status updated to running")
        
        # Parse dates
        start_date = parse_api_date(job.start_date)
        end_date = parse_api_date(job.end_date)
        
        if not start_date or not end_date:
            raise ValueError("❌ Date parsing error")
        
        logger.info(f"📅 [Job {job_id}] Date range: {job.start_date} to {job.end_date}")
        
        # Create crawler
        crawler = MojavezCrawler()
        
        # Get total count for display
        start_str = format_date_for_api(start_date)
        end_str = format_date_for_api(end_date)
        
        logger.info(f"🔍 [Job {job_id}] Fetching total records count...")
        total_count = crawler.get_records_count(
            start_str,
            end_str,
            job.province_id,
            job.township_id
        )
        
        job.total_records = total_count
        job.save()
        logger.info(f"📊 [Job {job_id}] Total records: {total_count}")
        
        # Use crawl_date_range which implements the splitting strategy
        # This will automatically split by date -> province -> city -> hours if needed
        logger.info(f"🔄 [Job {job_id}] Starting crawl with splitting strategy...")
        
        # Save callback function - saves records immediately to database
        def save_records_callback(records_batch):
            """Callback to save records immediately to database"""
            if not records_batch:
                return 0
            
            saved = 0
            with transaction.atomic():
                for record_data in records_batch:
                    # Skip if already exists (for resume)
                    if record_data.get('request_number') and CrawlRecord.objects.filter(
                        crawl_job=job,
                        request_number=record_data.get('request_number')
                    ).exists():
                        continue
                    
                    CrawlRecord.objects.create(
                        crawl_job=job,
                        request_number=record_data.get('request_number'),
                        applicant_name=record_data.get('applicant_name'),
                        user_image=record_data.get('user_image'),
                        license_title=record_data.get('license_title'),
                        organization_title=record_data.get('organization_title'),
                        province_id=record_data.get('province_id'),
                        province_title=record_data.get('province_title'),
                        township_id=record_data.get('township_id'),
                        township_title=record_data.get('township_title'),
                        responded_at=record_data.get('responded_at'),
                        status_id=record_data.get('status', {}).get('status_id') if isinstance(record_data.get('status'), dict) else None,
                        status_title=record_data.get('status', {}).get('status_title') if isinstance(record_data.get('status'), dict) else None,
                        status_slug=record_data.get('status', {}).get('status_slug') if isinstance(record_data.get('status'), dict) else None,
                        raw_data=record_data
                    )
                    saved += 1
            
            return saved
        
        # Progress callback function
        def update_progress_callback(fetched_count, current_page=0, total_pages=0):
            """Callback to update job progress during crawling"""
            try:
                job.refresh_from_db()
                # Get actual count from database
                actual_count = job.records.count()
                job.fetched_records = actual_count
                job.current_page = current_page
                if total_pages > 0:
                    job.total_pages = total_pages
                elif job.total_records > 0:
                    job.total_pages = (job.total_records + 20) // 21  # Estimate based on 21 per page
                
                if job.total_records > 0:
                    job.progress_percentage = int((actual_count / job.total_records) * 100)
                
                job.save()
                logger.info(f"📈 [Job {job_id}] Progress updated: {job.progress_percentage}% ({actual_count}/{job.total_records})")
            except Exception as e:
                logger.error(f"❌ [Job {job_id}] Error updating progress: {e}")
        
        # Check if we should use splitting strategy
        if total_count > crawler.MAX_RECORDS_PER_REQUEST:
            logger.info(f"📊 [Job {job_id}] Count ({total_count}) exceeds limit ({crawler.MAX_RECORDS_PER_REQUEST}). Using splitting strategy...")
            all_records = crawler.crawl_date_range(
                start_date,
                end_date,
                job.province_id,
                job.township_id,
                progress_callback=update_progress_callback,
                save_callback=save_records_callback
            )
        else:
            # If count is within limit, use direct pagination
            logger.info(f"📊 [Job {job_id}] Count ({total_count}) is within limit. Using direct pagination...")
            
            # Check if resuming - skip already fetched records
            if is_resume and existing_records_count > 0:
                # Get already fetched request_numbers to avoid duplicates
                existing_request_numbers = set(
                    job.records.values_list('request_number', flat=True).exclude(request_number__isnull=True)
                )
                logger.info(f"📋 [Job {job_id}] Found {len(existing_request_numbers)} existing records. Resuming from page {resume_from_page}")
            else:
                existing_request_numbers = set()
                resume_from_page = 1
            
            all_records = []
            page = resume_from_page
            
            while True:
                # Check if cancelled
                job.refresh_from_db()
                if job.status == 'cancelled':
                    logger.warning(f"⚠️ [Job {job_id}] Job was cancelled")
                    break
                
                # Fetch records with retry logic
                max_fetch_retries = 10
                fetch_retry_delay = 2
                result = None
                records = []
                pagination = {}
                
                for fetch_attempt in range(1, max_fetch_retries + 1):
                    try:
                        logger.info(f"📄 [Job {job_id}] Fetching page {page} (attempt {fetch_attempt}/{max_fetch_retries})...")
                        result = crawler.fetch_records(
                            start_str,
                            end_str,
                            job.province_id,
                            job.township_id,
                            page=page
                        )
                        
                        # Handle new response structure
                        if isinstance(result, dict):
                            records = result.get('records', [])
                            pagination = result.get('pagination', {})
                        else:
                            records = result if result else []
                            pagination = {}
                        
                        # Success - break retry loop
                        break
                        
                    except Exception as fetch_error:
                        if fetch_attempt < max_fetch_retries:
                            logger.warning(f"⚠️ [Job {job_id}] Error fetching page {page} (attempt {fetch_attempt}/{max_fetch_retries}): {fetch_error}. Retrying in {fetch_retry_delay}s...")
                            time.sleep(fetch_retry_delay)
                            fetch_retry_delay *= 2
                            continue
                        else:
                            logger.error(f"❌ [Job {job_id}] Failed to fetch page {page} after {max_fetch_retries} attempts: {fetch_error}")
                            page += 1
                            fetch_retry_delay = 2
                            continue
                
                if not records:
                    logger.info(f"ℹ️ [Job {job_id}] No more records found")
                    break
                
                # Filter out already fetched records (for resume)
                if is_resume and existing_request_numbers:
                    new_records = [r for r in records if r.get('request_number') not in existing_request_numbers]
                    skipped = len(records) - len(new_records)
                    if skipped > 0:
                        logger.info(f"⏭️ [Job {job_id}] Skipped {skipped} duplicate records on page {page}")
                    records = new_records
                
                # Save records immediately to database
                if records:
                    saved_count = save_records_callback(records)
                    logger.info(f"💾 [Job {job_id}] Saved {saved_count} records from page {page} to database")
                
                all_records.extend(records)
                
                # Update progress based on actual database count
                job.refresh_from_db()
                actual_count = job.records.count()
                job.fetched_records = actual_count
                job.current_page = page
                
                if job.total_records > 0:
                    job.progress_percentage = int((actual_count / job.total_records) * 100)
                    per_page = pagination.get('per_page', 21) or 21
                    job.total_pages = (job.total_records + per_page - 1) // per_page
                
                job.save()
                logger.info(f"📈 [Job {job_id}] Progress: {job.progress_percentage}% ({actual_count}/{job.total_records}) - Page {page}/{job.total_pages}")
                
                # Check if we should continue
                total_pages = pagination.get('total_pages', job.total_pages)
                if total_pages > 0 and page >= total_pages:
                    break
                
                if len(records) < 21 and page > 1:  # Assuming 21 per page
                    break
                
                page += 1
                time.sleep(0.5)
        
        # Records are already saved during crawling via save_callback
        # Just verify final count
        job.refresh_from_db()
        final_saved_count = job.records.count()
        logger.info(f"✅ [Job {job_id}] All records saved. Total in database: {final_saved_count}")
        
        # Complete crawl
        job.refresh_from_db()
        final_count = job.records.count()  # Get actual count from database
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.fetched_records = final_count
        job.progress_percentage = 100
        job.save()
        
        logger.info(f"✅ [Job {job_id}] Completed successfully! Total records: {final_count}")

        # After main crawl is completed, automatically start detail fetching task
        try:
            from .tasks import fetch_mojavez_details_for_job
            logger.info(f"🧾 [Job {job_id}] Triggering detail fetch task...")
            fetch_mojavez_details_for_job.delay(job_id)
        except Exception as e:
            logger.error(f"❌ [Job {job_id}] Failed to trigger detail fetch task: {e}")
        
        return {
            'job_id': job_id,
            'total_records': final_count,
            'status': 'completed'
        }
        
    except CrawlJob.DoesNotExist:
        logger.error(f"❌ [Job {job_id}] Job not found")
        return {'error': 'Job not found'}
    except Exception as e:
        # On error
        logger.error(f"❌ [Job {job_id}] Error: {str(e)}")
        try:
            job = CrawlJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()
        except:
            pass
        
        # Retry if needed (with exponential backoff)
        retry_count = self.request.retries
        countdown = min(60 * (2 ** retry_count), 600)  # Max 10 minutes
        logger.warning(f"🔄 [Job {job_id}] Retrying in {countdown} seconds... (attempt {retry_count + 1}/{self.max_retries})")
        raise self.retry(exc=e, countdown=countdown)


@shared_task(bind=True, max_retries=5)
def fetch_mojavez_details_for_job(self, job_id: int):
    """
    برای همه رکوردهای یک CrawlJob، صفحه track را با BeautifulSoup می‌خواند
    و جدول mojavez_detail را پر می‌کند.
    """
    try:
        job = CrawlJob.objects.get(id=job_id)
    except CrawlJob.DoesNotExist:
        logger.error(f"❌ [Detail Job {job_id}] CrawlJob not found")
        return {'job_id': job_id, 'status': 'not_found'}
    
    total = job.records.count()
    job.detail_total = total
    job.detail_processed = 0
    job.detail_errors = 0
    job.detail_status = 'running'
    job.save(update_fields=['detail_total', 'detail_processed', 'detail_errors', 'detail_status'])

    logger.info(f"🧾 [Detail Job {job_id}] Fetching mojavez_detail for {total} records...")
    
    crawler = MojavezCrawler()
    processed = 0
    errors = 0
    graphql_success = 0
    graphql_fail = 0
    html_fallback_used = 0
    html_fallback_failed = 0
    
    for record in job.records.all().iterator():
        if not record.request_number:
            continue
        
        # اگر قبلاً جزئیات ثبت شده، رد شو
        if hasattr(record, "detail"):
            continue
        
        try:
            # First try GraphQL-based detail fetch
            parsed = crawler.fetch_detail_via_graphql(record.request_number)

            # Fallback to HTML track page if GraphQL fails
            if not parsed:
                graphql_fail += 1
                html = crawler.fetch_track_page(record.request_number)
                if not html:
                    html_fallback_failed += 1
                    errors += 1
                    continue
                parsed = crawler.parse_track_html(html, request_number=record.request_number)
                parsed["source"] = "html"
                html_fallback_used += 1
            else:
                graphql_success += 1

            MojavezDetail.objects.create(
                crawl_record=record,
                request_number=parsed.get("request_number") or record.request_number,
                license_title=parsed.get("license_title"),
                organization_title=parsed.get("organization_title"),
                isic_code=parsed.get("isic_code"),
                issue_type=parsed.get("issue_type"),
                issued_at=parsed.get("issued_at"),
                expires_at=parsed.get("expires_at"),
                province_title=parsed.get("province_title_detail"),
                township_title=parsed.get("township_title_detail"),
                postal_code=parsed.get("postal_code"),
                business_address=parsed.get("business_address"),
                status_title=parsed.get("status_title"),
                status_slug=parsed.get("status_slug"),
                raw_data=parsed,
            )
            processed += 1

            # Update job detail progress
            job.detail_processed = processed
            job.save(update_fields=['detail_processed'])
            
            # تاخیر خیلی کوتاه برای احترام به سرور
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"❌ [Detail Job {job_id}] Error fetching detail for {record.request_number}: {e}")
            errors += 1
            job.detail_errors = errors
            job.save(update_fields=['detail_errors'])
    
    job.detail_status = 'completed'
    job.save(update_fields=['detail_status'])

    logger.info(
        "✅ [Detail Job %s] Done. Processed: %s, Errors: %s | GraphQL ok: %s, GraphQL fail: %s | HTML used: %s, HTML fail: %s",
        job_id,
        processed,
        errors,
        graphql_success,
        graphql_fail,
        html_fallback_used,
        html_fallback_failed,
    )
    return {
        "job_id": job_id,
        "processed": processed,
        "errors": errors,
    }
