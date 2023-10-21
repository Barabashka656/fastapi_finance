from celery import Celery
from app.data.config import settings

celery_app = Celery(
    'tasks', 
    broker=settings.REDIS_URL,
    include=["app.auth.service"]
)
