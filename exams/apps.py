from django.apps import AppConfig


class ExamsConfig(AppConfig):
    name = 'exams'

    def ready(self):
        from django.db.backends.signals import connection_created

        def set_sqlite_pragmas(sender, connection, **kwargs):
            if connection.vendor == 'sqlite':
                cursor = connection.cursor()
                cursor.execute('PRAGMA journal_mode=WAL;')
                cursor.execute('PRAGMA synchronous=NORMAL;')
                cursor.execute('PRAGMA busy_timeout=60000;')

        connection_created.connect(set_sqlite_pragmas)
