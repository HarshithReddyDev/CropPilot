from workers.celery_app import celery_app
from workers.tasks import *

__all__ = ["celery_app"]
