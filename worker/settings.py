from arq.connections import RedisSettings

class WorkerSettings:
    """
    Configuration for the ARQ worker.
    """
    redis_settings = RedisSettings()
    max_jobs = 10
    job_timeout = 300
    keep_result = 3600
