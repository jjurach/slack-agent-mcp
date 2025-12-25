"""
Slack Notifications - A simple Python library for Slack notifications.

This library provides easy-to-use functions for sending notifications
to Slack channels at application milestones.
"""

from .notifier import SlackNotifier, notify_milestone, notify_milestone_async
from .config import SlackConfig
from .exceptions import SlackNotificationError

__version__ = "0.1.0"
__all__ = [
    "SlackNotifier",
    "notify_milestone",
    "notify_milestone_async",
    "SlackConfig",
    "SlackNotificationError",
]