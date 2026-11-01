"""
Publication Schedule Planner
Calculates next optimal publication windows (11:00 AM IST & 7:00 PM IST)
and formats RFC 3339 timestamps for YouTube Data API scheduled publishing.
"""

from datetime import datetime, timedelta
import pytz
from typing import List, Tuple

DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_SLOTS = [(11, 0), (19, 0)] # 11:00 AM, 7:00 PM


class PublicationScheduler:
    @classmethod
    def get_next_publication_slots(
        cls,
        count: int = 2,
        timezone_str: str = DEFAULT_TIMEZONE,
        slots: List[Tuple[int, int]] = DEFAULT_SLOTS
    ) -> List[Tuple[datetime, str]]:
        """
        Determines the next upcoming publication datetime objects in IST
        and returns them paired with RFC 3339 UTC strings for YouTube API.
        """
        tz = pytz.timezone(timezone_str)
        now_local = datetime.now(tz)

        scheduled_slots = []
        days_ahead = 0

        while len(scheduled_slots) < count:
            target_date = now_local.date() + timedelta(days=days_ahead)
            for hour, minute in slots:
                slot_time = tz.localize(datetime(
                    target_date.year, target_date.month, target_date.day,
                    hour, minute, 0
                ))
                # Must be at least 45 minutes into the future
                if slot_time > now_local + timedelta(minutes=45):
                    # Convert to UTC RFC 3339 format
                    utc_time = slot_time.astimezone(pytz.utc)
                    rfc3339_str = utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                    scheduled_slots.append((slot_time, rfc3339_str))
                    if len(scheduled_slots) >= count:
                        break
            days_ahead += 1

        return scheduled_slots
