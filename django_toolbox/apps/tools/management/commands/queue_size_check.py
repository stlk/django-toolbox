import logging

from django.core.management.base import BaseCommand
from django_rq.utils import get_statistics

logger = logging.getLogger("queue_size")

class Command(BaseCommand):
    help = "Queue job count control"

    def add_arguments(self, parser):
        parser.add_argument('limit_value', type=int)

    def handle(self, *args, **options):
        statistics = get_statistics()
        limit_value = options.get('limit_value')

        for queue in statistics['queues']:
            if limit_value and queue['jobs'] >= limit_value:
                logger.warning(f"{queue['name']}: There is currently {queue['jobs']}.")

