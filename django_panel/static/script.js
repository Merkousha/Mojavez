// API Base URL
const API_BASE = '/api';

// CSRF helper (for Django session-auth APIs)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const CSRF_TOKEN = getCookie('csrftoken');

// SSE Connection
let eventSource = null;
let jobsData = {};  // Cache for jobs data
let workersCache = {};
let defaultQueue = 'default';

// Load stats and jobs on page load (only once)
document.addEventListener('DOMContentLoaded', () => {
    // Load initial data once
    loadWorkers();
    loadStats();
    loadJobs();
    
    // Connect to Server-Sent Events for real-time updates
    connectSSE();

    // Simple polling to keep job list (including detail progress) fresh
    setInterval(loadJobs, 5000);
});

// Load workers list
async function loadWorkers() {
    try {
        const response = await fetch(`${API_BASE}/jobs/workers/`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        defaultQueue = data.default_queue || 'default';
        workersCache = {};
        (data.workers || []).forEach(worker => {
            workersCache[worker.name] = worker.queues || [];
        });

        populateWorkerSelect('workerSelect', 'queueSelect');
    } catch (error) {
        console.error('Error loading workers:', error);
    }
}

function populateWorkerSelect(workerSelectId, queueSelectId) {
    const workerSelect = document.getElementById(workerSelectId);
    const queueSelect = document.getElementById(queueSelectId);
    if (!workerSelect || !queueSelect) {
        return;
    }

    const workerOptions = ['<option value="">خودکار</option>'];
    Object.keys(workersCache).forEach(workerName => {
        workerOptions.push(`<option value="${workerName}">${workerName}</option>`);
    });
    workerSelect.innerHTML = workerOptions.join('');

    updateQueueSelect(queueSelect, []);

    workerSelect.addEventListener('change', () => {
        const workerName = workerSelect.value;
        const queues = workersCache[workerName] || [];
        updateQueueSelect(queueSelect, queues);
    });
}

function updateQueueSelect(queueSelect, queues) {
    const options = ['<option value="">پیش فرض</option>'];
    const queueList = queues.length > 0 ? queues : [defaultQueue];
    queueList.forEach(queueName => {
        if (queueName) {
            options.push(`<option value="${queueName}">${queueName}</option>`);
        }
    });
    queueSelect.innerHTML = options.join('');
}

// Connect to SSE
function connectSSE() {
    if (eventSource) {
        eventSource.close();
    }
    
    eventSource = new EventSource(`${API_BASE}/jobs/events/`);
    
    eventSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'stats') {
                updateStats(data.data);
            } else if (data.type === 'job_update') {
                updateJobProgress(data.data);
                // Also update the job in our cache
                if (jobsData[data.data.id]) {
                    Object.assign(jobsData[data.data.id], data.data);
                }
            } else if (data.type === 'error') {
                console.error('SSE Error:', data.message);
            }
        } catch (e) {
            // Ignore heartbeat messages and other non-JSON data
        }
    };
    
    eventSource.onerror = function(event) {
        console.error('SSE Connection error, reconnecting...');
        eventSource.close();
        setTimeout(connectSSE, 3000);  // Reconnect after 3 seconds
    };
    
    console.log('✅ SSE Connected - Real-time updates enabled');
}

// Close SSE on page unload
window.addEventListener('beforeunload', () => {
    if (eventSource) {
        eventSource.close();
    }
});

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/jobs/stats/`);
        const stats = await response.json();
        updateStats(stats);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Update statistics display
function updateStats(stats) {
    document.getElementById('totalJobs').textContent = stats.total_jobs;
    document.getElementById('runningJobs').textContent = stats.running_jobs;
    document.getElementById('completedJobs').textContent = stats.completed_jobs;
    document.getElementById('totalRecords').textContent = stats.total_records.toLocaleString('fa-IR');
}

// Load jobs list (only called once on page load)
async function loadJobs() {
    try {
        const response = await fetch(`${API_BASE}/jobs/`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Handle DRF pagination format
        let jobs = [];
        if (Array.isArray(data)) {
            jobs = data;
        } else if (data.results) {
            jobs = data.results;
        } else {
            jobs = [];
        }
        
        // Cache jobs data
        jobsData = {};
        jobs.forEach(job => {
            jobsData[job.id] = job;
        });
        
        const jobsList = document.getElementById('jobsList');
        
        if (jobs.length === 0) {
            jobsList.innerHTML = '<div class="loading">هیچ کراولی وجود ندارد</div>';
            return;
        }
        
        renderJobs(jobs);
    } catch (error) {
        console.error('Error loading jobs:', error);
        document.getElementById('jobsList').innerHTML = `<div class="loading">خطا در بارگذاری: ${error.message}</div>`;
    }
}

// Render jobs list
function renderJobs(jobs) {
    const jobsList = document.getElementById('jobsList');
    jobsList.innerHTML = jobs.map(job => createJobCard(job)).join('');
}

// Create job card HTML
function createJobCard(job) {
    const statusClass = `status-${job.status}`;
    const statusText = {
        'pending': '⏳ در انتظار',
        'running': '🔄 در حال اجرا',
        'completed': '✅ تکمیل شده',
        'failed': '❌ ناموفق',
        'cancelled': '🚫 لغو شده'
    }[job.status] || job.status;
    
    const progress = job.progress_percentage || 0;
    const location = job.province_name || job.province_id || 'همه';
    const city = job.township_name || job.township_id || 'همه';
    const detailTotal = job.detail_total || 0;
    const detailProcessed = job.detail_processed || 0;
    const detailErrors = job.detail_errors || 0;
    const detailStatus = job.detail_status || 'pending';
    const detailPercent = detailTotal > 0 ? Math.floor((detailProcessed / detailTotal) * 100) : 0;
    const hasWorker = !!(job.target_worker || job.target_queue);
    const workerDisplay = job.target_worker || (job.target_queue ? `صف: ${job.target_queue}` : null) || '—';
    const canStart = job.status === 'pending' || job.status === 'failed' || job.status === 'cancelled';
    const workerNames = Object.keys(workersCache);
    if (job.target_worker && !workerNames.includes(job.target_worker)) {
        workerNames.push(job.target_worker);
    }
    const workerOptions = workerNames.map(name =>
        `<option value="${name}" ${job.target_worker === name ? ' selected' : ''}>${name}</option>`
    ).join('');
    
    return `
        <div class="job-card" id="job-${job.id}">
            <div class="job-header">
                <div class="job-title">${job.name}</div>
                <div class="job-status ${statusClass}">${statusText}</div>
            </div>
            
            <div class="job-info">
                <div class="job-info-item">
                    <span class="job-info-label">بازه زمانی:</span>
                    <span class="job-info-value">${job.start_date} تا ${job.end_date}</span>
                </div>
                <div class="job-info-item">
                    <span class="job-info-label">موقعیت:</span>
                    <span class="job-info-value">${location} - ${city}</span>
                </div>
                <div class="job-info-item">
                    <span class="job-info-label">رکوردها:</span>
                    <span class="job-info-value">${job.fetched_records.toLocaleString('fa-IR')} / ${job.total_records.toLocaleString('fa-IR')}</span>
                </div>
                <div class="job-info-item">
                    <span class="job-info-label">ورکر:</span>
                    <span class="job-info-value">${hasWorker ? workerDisplay : '— (بدون ورکر)'}</span>
                    ${job.target_queue ? `<span class="job-info-value" style="margin-right:8px">صف: ${job.target_queue}</span>` : ''}
                </div>
                ${canStart && !hasWorker ? `
                <div class="job-info-item assign-worker-row">
                    <span class="job-info-label">اختصاص ورکر:</span>
                    <select id="assign-worker-${job.id}" class="assign-worker-select">
                        <option value="">خودکار (صف پیش‌فرض)</option>
                        ${workerOptions}
                    </select>
                </div>
                ` : ''}
                ${canStart && hasWorker ? `
                <div class="job-info-item assign-worker-row">
                    <span class="job-info-label">تغییر ورکر:</span>
                    <select id="assign-worker-${job.id}" class="assign-worker-select">
                        <option value="">همان ورکر فعلی</option>
                        ${workerOptions}
                    </select>
                </div>
                ` : ''}
                ${detailTotal > 0 || detailStatus === 'running' ? `
                <div class="job-info-item">
                    <span class="job-info-label">جزئیات مجوز:</span>
                    <span class="job-info-value">
                        ${detailProcessed.toLocaleString('fa-IR')} / ${detailTotal.toLocaleString('fa-IR')}
                        ${detailErrors ? ` (خطا: ${detailErrors.toLocaleString('fa-IR')})` : ''}
                    </span>
                </div>
                ` : ''}
                <div class="job-info-item">
                    <span class="job-info-label">تاریخ ایجاد:</span>
                    <span class="job-info-value">${new Date(job.created_at).toLocaleString('fa-IR')}</span>
                </div>
            </div>
            
            ${job.status === 'running' ? `
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${progress}%">${progress}%</div>
                </div>
                <div style="text-align: center; margin-top: 5px; color: #666; font-size: 0.9em;">
                    صفحه ${job.current_page} از ${job.total_pages || '?'}
                </div>
            ` : ''}
            
            ${detailStatus === 'running' && detailTotal > 0 ? `
                <div class="progress-bar" style="margin-top: 6px; background: #f0f4ff;">
                    <div class="progress-fill" style="width: ${detailPercent}%; background: #007bff;">
                        ${detailPercent}%
                    </div>
                </div>
                <div style="text-align: center; margin-top: 3px; color: #666; font-size: 0.85em;">
                    در حال دریافت جزئیات مجوز...
                </div>
            ` : ''}
            
            ${job.error_message ? `
                <div style="background: #fee; padding: 10px; border-radius: 5px; margin: 10px 0; color: #c33;">
                    <strong>خطا:</strong> ${job.error_message}
                </div>
            ` : ''}
            
            <div class="job-actions">
                ${job.status === 'pending' ? `
                    <button class="btn btn-success" onclick="startJob(${job.id})">▶️ شروع</button>
                ` : ''}
                ${(job.status === 'failed' || job.status === 'cancelled') ? `
                    <button class="btn btn-success" onclick="startJob(${job.id})">▶️ شروع مجدد</button>
                ` : ''}
                ${job.status === 'running' ? `
                    <button class="btn btn-danger" onclick="cancelJob(${job.id})">⏹️ لغو</button>
                    <button class="btn btn-primary" onclick="requeueJob(${job.id})" title="اگر تسک روی Redis نیست، دوباره به صف بفرست">📤 ارسال مجدد به صف</button>
                    <button class="btn btn-secondary" onclick="checkTaskState(${job.id})" title="وضعیت تسک در Celery/Redis">🔍 وضعیت تسک</button>
                ` : ''}
                <button class="btn btn-secondary" onclick="viewRecords(${job.id})">📄 رکوردها</button>
                ${job.status === 'completed' ? `
                    <button class="btn btn-primary" onclick="fetchDetails(${job.id})">📥 جزئیات مجوز</button>
                ` : ''}
                <button class="btn btn-danger" onclick="deleteJob(${job.id})">🗑️ حذف</button>
            </div>
        </div>
    `;
}

// Create job form handler
document.getElementById('createJobForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('jobName').value,
        start_date: document.getElementById('startDate').value,
        end_date: document.getElementById('endDate').value,
        province_id: document.getElementById('provinceId').value ? parseInt(document.getElementById('provinceId').value) : null,
        township_id: document.getElementById('townshipId').value ? parseInt(document.getElementById('townshipId').value) : null,
        province_name: document.getElementById('provinceName').value || null,
        township_name: document.getElementById('townshipName').value || null,
        target_worker: document.getElementById('workerSelect').value || null,
        target_queue: document.getElementById('queueSelect').value || null
    };
    
    try {
        const response = await fetch(`${API_BASE}/jobs/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            alert('✅ کراول با موفقیت ایجاد شد!');
            document.getElementById('createJobForm').reset();
            loadJobs();
            loadStats();
        } else {
            const error = await response.json();
            alert('❌ خطا: ' + (error.detail || 'خطای نامشخص'));
        }
    } catch (error) {
        alert('❌ خطا در ایجاد کراول: ' + error.message);
    }
});

// Start job
async function startJob(jobId) {
    const assignSelect = document.getElementById(`assign-worker-${jobId}`);
    let targetWorker = null;
    let targetQueue = null;
    if (assignSelect && assignSelect.value) {
        targetWorker = assignSelect.value;
        const queues = workersCache[targetWorker];
        if (queues && queues.length > 0) {
            targetQueue = queues[0];
        }
    }
    const body = {};
    if (targetWorker) body.target_worker = targetWorker;
    if (targetQueue) body.target_queue = targetQueue;

    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}/start/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
            },
            body: Object.keys(body).length ? JSON.stringify(body) : undefined,
        });
        
        if (response.ok) {
            alert('✅ کراول شروع شد!' + (targetWorker ? ` (ورکر: ${targetWorker})` : ''));
            loadJobs();
        } else {
            const error = await response.json();
            alert('❌ خطا: ' + (error.detail || error.error || 'خطای نامشخص'));
        }
    } catch (error) {
        alert('❌ خطا در شروع کراول: ' + error.message);
    }
}

// Check Celery/Redis task state for a job
async function checkTaskState(jobId) {
    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}/task_state/`);
        const data = await response.json();
        const lost = data.lost ? ' ⚠️ تسک احتمالاً از صف رفته' : '';
        alert(`وضعیت تسک: ${data.state || '—'}\n${data.message || ''}${lost}\n${data.task_id ? 'Task ID: ' + data.task_id : ''}`);
    } catch (error) {
        alert('❌ خطا در بررسی وضعیت تسک: ' + error.message);
    }
}

// Re-queue job to Redis (for running jobs whose task was lost from queue)
async function requeueJob(jobId) {
    if (!confirm('این job دوباره به صف Redis فرستاده می‌شود و از همان checkpoint ادامه پیدا می‌کند. ادامه؟')) {
        return;
    }
    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}/requeue/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
            },
        });
        if (response.ok) {
            const data = await response.json();
            alert('✅ ارسال مجدد به صف انجام شد.\nTask ID: ' + (data.task_id || '—'));
            loadJobs();
        } else {
            const error = await response.json();
            alert('❌ خطا: ' + (error.error || error.detail || 'خطای نامشخص'));
        }
    } catch (error) {
        alert('❌ خطا در ارسال مجدد به صف: ' + error.message);
    }
}

// Cancel job
async function cancelJob(jobId) {
    if (!confirm('آیا مطمئن هستید که می‌خواهید این کراول را لغو کنید؟')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}/cancel/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
            },
        });
        
        if (response.ok) {
            alert('✅ کراول لغو شد!');
            loadJobs();
        } else {
            const error = await response.json();
            alert('❌ خطا: ' + (error.detail || 'خطای نامشخص'));
        }
    } catch (error) {
        alert('❌ خطا: ' + error.message);
    }
}

// Delete job
async function deleteJob(jobId) {
    if (!confirm('⚠️ آیا مطمئن هستید که می‌خواهید این کراول و تمام رکوردهایش را حذف کنید؟')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
            },
        });
        
        if (response.ok) {
            alert('✅ کراول حذف شد!');
            loadJobs();
            loadStats();
        } else {
            const error = await response.json();
            alert('❌ خطا: ' + (error.detail || 'خطای نامشخص'));
        }
    } catch (error) {
        alert('❌ خطا: ' + error.message);
    }
}

// View records
async function viewRecords(jobId) {
    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}/records/?limit=100`);
        const records = await response.json();
        
        const modal = document.getElementById('recordsModal');
        const recordsList = document.getElementById('recordsList');
        
        if (records.length === 0) {
            recordsList.innerHTML = '<div class="loading">هیچ رکوردی وجود ندارد</div>';
        } else {
            recordsList.innerHTML = records.map(record => `
                <div class="record-item">
                    <div><strong>شماره درخواست:</strong> ${record.request_number || '-'}</div>
                    <div><strong>نام متقاضی:</strong> ${record.applicant_name || '-'}</div>
                    <div><strong>عنوان مجوز:</strong> ${record.license_title || '-'}</div>
                    <div><strong>سازمان:</strong> ${record.organization_title || '-'}</div>
                    <div><strong>استان/شهر:</strong> ${record.province_title || '-'} / ${record.township_title || '-'}</div>
                    <div><strong>وضعیت:</strong> ${record.status_title || '-'}</div>
                    <div><strong>تاریخ پاسخ:</strong> ${record.responded_at || '-'}</div>
                </div>
            `).join('');
        }
        
        modal.style.display = 'block';
    } catch (error) {
        alert('❌ خطا در بارگذاری رکوردها: ' + error.message);
    }
}

// Fetch mojavez_detail for a job
async function fetchDetails(jobId) {
    if (!confirm('برای این کراول، جزئیات مجوزها از سایت qr.mojavez.ir خوانده و در جدول mojavez_detail ذخیره شود؟')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/jobs/${jobId}/fetch_details/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
            },
        });

        if (response.ok) {
            alert('✅ تسک دریافت جزئیات مجوزها شروع شد. چند لحظه بعد، رکوردها در دیتابیس پر می‌شوند.');
        } else {
            const error = await response.json();
            alert('❌ خطا در شروع تسک جزئیات: ' + (error.detail || error.error || 'خطای نامشخص'));
        }
    } catch (error) {
        alert('❌ خطا در اتصال برای دریافت جزئیات: ' + error.message);
    }
}

// Close modal
function closeModal() {
    document.getElementById('recordsModal').style.display = 'none';
}

// Refresh jobs (manual refresh button)
function refreshJobs() {
    loadJobs();
    loadStats();
    console.log('🔄 Manual refresh triggered');
}

// Update job progress from SSE
function updateJobProgress(jobData) {
    const jobId = jobData.id;
    const progress = jobData.progress_percentage || 0;
    const fetched = jobData.fetched_records || 0;
    const total = jobData.total_records || 0;
    const currentPage = jobData.current_page || 0;
    const totalPages = jobData.total_pages || 0;
    
    // Update progress bar
    const progressFill = document.getElementById(`progress-fill-${jobId}`);
    const progressInfo = document.getElementById(`progress-info-${jobId}`);
    
    if (progressFill) {
        progressFill.style.width = `${progress}%`;
        progressFill.textContent = `${progress}%`;
    }
    
    if (progressInfo) {
        progressInfo.textContent = `${fetched.toLocaleString('fa-IR')} / ${total.toLocaleString('fa-IR')} رکورد - صفحه ${currentPage} از ${totalPages || '?'}`;
    }
    
    // Update records count in job info section
    const jobCard = document.getElementById(`job-${jobId}`);
    if (jobCard) {
        const recordsValue = jobCard.querySelector('.job-info-item:nth-child(3) .job-info-value');
        if (recordsValue) {
            recordsValue.textContent = `${fetched.toLocaleString('fa-IR')} / ${total.toLocaleString('fa-IR')}`;
        }
    }
    
    // If job completed, reload jobs list once to show updated status
    if (jobData.status === 'completed' || jobData.status === 'failed') {
        setTimeout(() => {
            loadJobs();  // Reload once to show final status
        }, 1000);
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('recordsModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}
