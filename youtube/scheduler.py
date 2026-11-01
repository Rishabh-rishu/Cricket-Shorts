"""
Publication Schedule Planner
Calculates next optimal publication windows (12:00 PM IST & 6:00 PM IST)
and formats RFC 3339 timestamps for YouTube Data API scheduled publishing.
"""

import os
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import pytz
import yaml

DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_SLOTS = [(12, 0), (18, 0)]  # 12:00 PM, 6:00 PM IST


class PublicationScheduler:
    @classmethod
    def load_configured_slots(cls, config_path: str = "config/settings.yaml") -> Tuple[str, List[Tuple[int, int]]]:
        """Loads timezone and daily slots from config/settings.yaml if available."""
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                tz_str = cfg.get("publishing", {}).get("timezone", DEFAULT_TIMEZONE)
                raw_slots = cfg.get("publishing", {}).get("daily_slots", ["12:00", "18:00"])
                slots = []
                for s in raw_slots:
                    parts = str(s).split(":")
                    slots.append((int(parts[0]), int(parts[1])))
                return tz_str, slots
            except Exception:
                pass
        return DEFAULT_TIMEZONE, DEFAULT_SLOTS

    @classmethod
    def get_next_publication_slots(
        cls,
        count: int = 2,
        timezone_str: Optional[str] = None,
        slots: Optional[List[Tuple[int, int]]] = None
    ) -> List[Tuple[datetime, str]]:
        """
        Determines the next upcoming publication datetime objects in IST
        and returns them paired with RFC 3339 UTC strings for YouTube API.
        """
        if timezone_str is None or slots is None:
            cfg_tz, cfg_slots = cls.load_configured_slots()
            timezone_str = timezone_str or cfg_tz
            slots = slots or cfg_slots

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
                # Must be at least 20 minutes into the future for YouTube scheduled publishing
                if slot_time > now_local + timedelta(minutes=20):
                    utc_time = slot_time.astimezone(pytz.utc)
                    rfc3339_str = utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                    scheduled_slots.append((slot_time, rfc3339_str))
                    if len(scheduled_slots) >= count:
                        break
            days_ahead += 1

        return scheduled_slots

    @classmethod
    def get_immediate_or_next_slot(
        cls,
        timezone_str: Optional[str] = None,
        slots: Optional[List[Tuple[int, int]]] = None
    ) -> Tuple[datetime, Optional[str]]:
        """
        Determines if the current execution is within a target publishing window.
        If executed near 12:00 PM or 6:00 PM (within 30 mins), returns (now_local, None) for immediate release.
        Otherwise, returns the next scheduled slot with RFC 3339 string.
        """
        if timezone_str is None or slots is None:
            cfg_tz, cfg_slots = cls.load_configured_slots()
            timezone_str = timezone_str or cfg_tz
            slots = slots or cfg_slots

        tz = pytz.timezone(timezone_str)
        now_local = datetime.now(tz)

        for hour, minute in slots:
            slot_today = tz.localize(datetime(
                now_local.year, now_local.month, now_local.day,
                hour, minute, 0
            ))
            # Within ±30 minutes of a scheduled slot
            if abs((now_local - slot_today).total_seconds()) <= 1800:
                return now_local, None

        upcoming = cls.get_next_publication_slots(count=1, timezone_str=timezone_str, slots=slots)
        return upcoming[0]
