# Celery Workers on Kubernetes — Queues and Restarts

## What happens to queues when workers (pods) restart?

- **Queues live in Redis**, not in the workers. When you replace worker pods (e.g. after an update or scale change), **pending tasks stay in Redis**.
- **New pods** start new Celery workers that connect to the **same Redis** and consume from the same queues. They will pick up any **pending** tasks automatically.
- **In-flight tasks** (already delivered to a worker that then died): with **`acks_late=True`**, the task is acknowledged only after it finishes. If the worker pod is killed before that, the message is **re-queued** and another worker will run it. Your crawl jobs support **resume** (by page and existing records), so re-running is safe.

So: **restarting workers does not lose the queue**. Pending tasks are consumed by new workers; in-flight tasks are redelivered when using `acks_late=True`.

## Why did I see "missed heartbeat" and the process stop?

- Workers send periodic heartbeats. When they are very busy (long HTTP calls to the API, heavy DB writes for 1.4M records), they may not send a heartbeat in time and get reported as "missed heartbeat". That can lead to the broker/monitor treating them as dead even though they are still working.
- To reduce this:
  - Workers are started with **`--without-heartbeat`** in `Dockerfile.worker`, so they do not participate in heartbeat checks and are not marked dead just because they are busy.
  - Optionally, `CELERY_WORKER_HEARTBEAT_INTERVAL` is increased in settings (e.g. 60s) if you run *with* heartbeat.
- You can still use **Kubernetes liveness/readiness probes** (e.g. HTTP or a small Celery ping) to detect truly dead pods.

## Ensuring the process keeps working after updates

1. **Use the same Redis broker** for all workers before and after the rollout. New pods must have the same `CELERY_BROKER_URL` (e.g. via env/ConfigMap/Secret).
2. **Keep `acks_late=True`** on long-running tasks (`run_crawl_job`, `fetch_mojavez_details_for_job`) so that if a pod is killed mid-task, the task is re-queued and another worker (or the same after restart) will run it; job resume logic will continue from the last checkpoint.
3. **Graceful shutdown**: On SIGTERM, Celery finishes the current task and then exits. Give a sufficiently long **terminationGracePeriodSeconds** in your Pod spec (e.g. 600–900 seconds) so that a long-running crawl page can finish before the process is killed.
4. **Optional**: Set **resource limits** (memory/CPU) and **`--max-tasks-per-child=50`** (already in Dockerfile) so worker processes are recycled and memory does not grow unbounded over millions of records.

## Worker name (CELERY_WORKER_NAME) — دیدن ورکرها هنگام اضافه کردن تسک

وقتی تسک اضافه می‌کنید، لیست ورکرها از Celery (inspect) گرفته می‌شود. به‌طور پیش‌فرض نام ورکر از hostname پاد می‌آید (مثلاً `celery@worker10-85c96d5444-7kdr9`). اگر env زیر را روی هر پاد/Deployment ست کنید، نام خوانا در پنل دیده می‌شود:

- **`CELERY_WORKER_NAME`** — نام نمایشی ورکر (مثال: `worker-tehran`, `worker-1`, `worker-crawl-a`).

در Dockerfile.worker ورکر با `-n ${CELERY_WORKER_NAME:-worker}@%h` استارت می‌شود؛ یعنی نام نود می‌شود مثلاً `worker-tehran@<hostname>`. در API لیست ورکرها (`/api/jobs/workers/`) و در dropdown «ورکر مقصد» همین نام‌ها نمایش داده می‌شوند.

**مثال در K8s (Deployment):**

```yaml
env:
  - name: CELERY_WORKER_NAME
    value: "worker-tehran"
  # یا برای چند رپلیکا با نام یکسان ولی یونیک با hostname:
  # value: "worker-crawl"
```

اگر چند پاد با یک `CELERY_WORKER_NAME` داشته باشید، به‌خاطر `@%h` نام هر ورکر یونیک می‌ماند (مثلاً `celery@worker-tehran@worker10-85c96d5444-7kdr9`). اگر هر Deployment فقط یک replica داشته باشد و به هر کدام یک `CELERY_WORKER_NAME` جدا بدهید (مثلاً worker-1 تا worker-19)، در لیست ورکرها همان نام‌های خوانا را می‌بینید.

## چطور بفهمم ورکرها واقعاً کار می‌کنند و خطا نخورده‌اند؟

### ۱. از روی لاگ همین ورکر

- **ورکر آماده است** اگر این را دیدید:  
  `Worker19@worker19-... ready.`  
  یعنی به Redis وصل شده و منتظر تسک است. بعدش فقط پیام‌های `mingle: sync with ...` یا `sync with WorkerX@...` می‌آید تا وقتی تسکی به این ورکر نرسد.

- **وقتی تسکی به این ورکر می‌رسد** در لاگ باید یکی از این‌ها را ببینید:
  - `Received task: jobs.tasks.run_crawl_job[...]` (شروع دریافت تسک)
  - `🚀 [Job 123] Starting crawl job...` (شروع اجرای واقعی از کد ما)
  - در حین کار: `📄 [Job 123] Fetching page 5...` و `📈 [Job 123] Progress: 10%...`
  - در پایان موفق: `✅ [Job 123] Completed successfully!` و در لاگ Celery: `Task jobs.tasks.run_crawl_job[...] succeeded in ...`
  - در صورت خطا: `❌ [Job 123] Error: ...` و در لاگ Celery: `Task ... FAILED: ...`

اگر بعد از `ready.` فقط `sync with WorkerX` می‌بینید و هیچ `Received task` یا `🚀 [Job ...]` نیست، یعنی **هنوز تسکی به این ورکر نفرستاده‌اید**؛ ورکر سالم است، فقط بیکار.

### ۲. Flower (پنل وب برای Celery)

با **Flower** می‌توانید ببینید کدام ورکرها آنلاین‌اند، الان چه تسکی روی کدام ورکر در حال اجراست و کدام تسک‌ها موفق/ناموفق شده‌اند.

```bash
# روی همان Redis پروژه
celery -A crawler_panel flower --broker=<REDIS_URL>
```

بعد در مرورگر آدرس Flower را باز کنید (مثلاً همان پورتی که Flower روی آن بالا آمده). در تب Workers لیست ورکرها و وضعیت آنلاین/آفلاین، و در تب Tasks لیست تسک‌های در حال اجرا و انجام‌شده (و در صورت خطا، وضعیت Failed) را می‌بینید.

### ۳. از طریق پنل Django

در صفحه لیست کراول‌ها وضعیت هر job (در انتظار / در حال اجرا / تکمیل شده / ناموفق) و پیشرفت (مثلاً درصد و صفحه) نمایش داده می‌شود. اگر jobی «در حال اجرا» است و عدد پیشرفت عوض می‌شود، یعنی حداقل یک ورکر آن تسک را در حال اجرا دارد.

### ۴. هشدار امنیتی در لاگ (اجرا با root)

اگر این را دیدید:  
`SecurityWarning: You're running the worker with superuser privileges`  
یعنی ورکر با کاربر root داخل کانتینر اجرا شده. برای رفع این هشدار در Dockerfile.worker یک کاربر غیر root اضافه شده و ورکر با همان کاربر اجرا می‌شود؛ بعد از rebuild تصویر این هشدار نباید بیاید.

---

## Summary

| Question | Answer |
|----------|--------|
| Where are the queues? | In **Redis**. Restarting workers does not delete them. |
| Do new pods get the same tasks? | Yes. New workers consume from the same Redis queues. |
| What about tasks that were running when the pod died? | With **acks_late=True**, they are **re-queued** and run again; your job resume handles duplicates and progress. |
| How to avoid "missed heartbeat" stopping the process? | Use **`--without-heartbeat`** (in Dockerfile) and/or higher **CELERY_WORKER_HEARTBEAT_INTERVAL**. |
| How to see readable worker names when adding a task? | Set **CELERY_WORKER_NAME** in each pod/Deployment (e.g. `worker-tehran`, `worker-1`). |
| How to know if workers are really working and not erroring? | Check logs for `Received task` / `🚀 [Job …]` / `succeeded` / `FAILED`; or use **Flower**; or check job status in the Django panel. |
| Workers are "ready" but no tasks run? | Ensure **CELERY_DEFAULT_QUEUE** matches the queue workers consume. Default in Celery is **`celery`**; if the app sent tasks to `default`, workers (listening to `celery`) would never receive them. Set `CELERY_DEFAULT_QUEUE=celery` (or run workers with `-Q default` if you keep queue name `default`). |
