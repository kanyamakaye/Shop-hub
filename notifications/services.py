from .models import Notification


def notify(user, title, message, notification_type=Notification.NotificationType.GENERAL, tenant=None):
    return Notification.objects.create(
        user=user, tenant=tenant or getattr(user, 'tenant', None),
        title=title, message=message, notification_type=notification_type,
    )
