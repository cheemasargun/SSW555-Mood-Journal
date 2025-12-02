from datetime import datetime
from extensions import db
from models_notification import NotificationSettings

class NotificationManager:

    @staticmethod
    def send_notification(last_notification):
        last_notification["message"] = "It's time to log your mood entry!"
        print("TOAST NOTIFICATION TRIGGERED")

    @staticmethod
    def schedule_job(scheduler, last_notification):
        """Schedules the reminder based on DB settings."""
        with scheduler.app.app_context():
            settings = NotificationSettings.query.first()
            if not settings or not settings.enabled:
                return

            # ALWAYS remove the old job first (this solves ConflictingIdError)
            try:
                scheduler.remove_job("daily-reminder")
            except:
                pass

            # Now safely add a fresh job
            scheduler.add_job(
                id="daily-reminder",
                func=lambda: NotificationManager.send_notification(last_notification),
                trigger="cron",
                hour=settings.scheduled_hour,
                minute=settings.scheduled_minute,
            )
            
    @staticmethod
    def disable_job(scheduler):
        try:
            scheduler.remove_job("daily-reminder")
        except:
            pass