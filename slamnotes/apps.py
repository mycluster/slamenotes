from django.apps import AppConfig


class SlamnotesConfig(AppConfig):
    name = 'slamnotes'
    verbose_name = "Slam Notes"

    def ready(self):
        pass
