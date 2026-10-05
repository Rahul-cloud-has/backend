from django.apps import AppConfig


class ProskillsConfig(AppConfig):
    name = 'proskills'

    def ready(self):
        from . import signals  # noqa: F401
