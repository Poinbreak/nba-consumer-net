import os
import sys
import threading

from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Opening a Supabase connection costs ~2 s; warm the pool in the background so the first page load is fast.
        # RUN_MAIN guard: runserver's autoreloader imports apps twice, only warm in the serving process.
        if os.environ.get('RUN_MAIN') == 'false' or not any('runserver' in a or 'daphne' in a for a in sys.argv):
            return              # tests, management commands and scripts must not hold pooled connections

        def warm():
            try:
                from .db import parallel, current_season
                parallel(*[('SELECT 1', None)] * 4)
                current_season()
                from . import ask
                ask._players(); ask._teams()      # name indexes used by the natural-language search
            except Exception as e:  # never block startup on a cold/unreachable DB
                print(f'[api] pool warm-up skipped: {e}')

        threading.Thread(target=warm, daemon=True).start()
