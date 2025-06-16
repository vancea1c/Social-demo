from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    name = 'Notifications'

    def ready(self):
        import Notifications.signals 