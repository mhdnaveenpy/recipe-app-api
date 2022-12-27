"""
DJANGO Command to wait for the database to be available.
"""
import time

from psycopg2 import OperationalError as Psycopg2OpError

from django.db.utils import OperationalError
from django.core.management import BaseCommand


class Command(BaseCommand):
    """
    DJANGO COMMAND TO WAIT FOR DATABASE
    """

    def handle(self, *args, **kwargs):
        """Entrypoint for command."""

        self.stdout.write('Waiting for database...')

        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2OpError, OperationalError):
                self.stdout.write('Database unavailable, \
                    waiting for 1 secound...')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database available!'))
