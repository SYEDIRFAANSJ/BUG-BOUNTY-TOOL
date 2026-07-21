task_acks_late = True
task_reject_on_worker_lost = True
task_default_retry_delay = 60
task_time_limit = 1500       # 25 min hard kill
task_soft_time_limit = 1200  # 20 min SoftTimeLimitExceeded
broker_url = 'redis://redis:6379/0'  # will be overridden by settings
result_backend = 'redis://redis:6379/0'
