from django.apps import AppConfig


class PointsExtensionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "points"
    name = "bias_ext_points.backend"
    verbose_name = "Bias Points Extension"


