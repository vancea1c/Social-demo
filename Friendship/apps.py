from django.apps import AppConfig

class FriendshipConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Friendship'

    def ready(self):
        import Friendship.signals  
