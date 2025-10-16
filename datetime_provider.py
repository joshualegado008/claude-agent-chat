"""
DateTime Provider - Inject current time context into agent conversations
Eliminates confusion about "today", "this week", "recent", etc.
"""

from datetime import datetime, timezone

# Try Python 3.9+ zoneinfo
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for Python < 3.9
    try:
        import pytz

        # Create ZoneInfo-like wrapper for pytz
        class ZoneInfo:
            def __init__(self, tz_name):
                if tz_name == 'UTC':
                    self.tzinfo = pytz.UTC
                else:
                    self.tzinfo = pytz.timezone(tz_name)

            def __call__(self):
                return self.tzinfo

    except ImportError:
        # Ultimate fallback: UTC only
        class ZoneInfo:
            def __init__(self, tz_name):
                if tz_name != 'UTC':
                    print(f"⚠️  pytz not available, using UTC instead of {tz_name}")
                self.tzinfo = timezone.utc

            def __call__(self):
                return self.tzinfo


class DateTimeProvider:
    """
    Provides formatted datetime strings for agent context.

    Features:
    - Configurable timezone
    - Multiple format options
    - Relative time descriptions
    - Helpful context for agents
    """

    def __init__(self, config: dict):
        """
        Initialize datetime provider.

        Args:
            config: Configuration dict with 'timezone' and 'format'
        """
        timezone_str = config.get('timezone', 'UTC')

        try:
            tz = ZoneInfo(timezone_str)
            # Handle both real ZoneInfo and our wrapper
            self.timezone = tz() if hasattr(tz, '__call__') else tz
        except Exception as e:
            # Fallback to UTC
            print(f"⚠️  Invalid timezone '{timezone_str}', using UTC: {e}")
            try:
                tz = ZoneInfo('UTC')
                self.timezone = tz() if hasattr(tz, '__call__') else tz
            except:
                self.timezone = timezone.utc

        self.format_str = config.get(
            'format',
            '%A, %B %d, %Y, %H:%M:%S %Z'
        )

    def get_current_datetime(self) -> str:
        """
        Get formatted current datetime with context.

        Returns:
            Formatted string with datetime and helpful context
        """
        now = datetime.now(self.timezone)

        # Format according to config
        formatted = now.strftime(self.format_str)

        # Extract components for context
        day_name = now.strftime('%A')
        month_name = now.strftime('%B')
        day = now.day
        year = now.year

        # Build context string
        context = (
            f"Current Date & Time: {formatted}\n"
            f"Context: It is {day_name}, {month_name} {day}, {year}. "
            f"Use this for time-aware reasoning about 'today', 'this week', 'recent', etc."
        )

        return context

    def get_iso_timestamp(self) -> str:
        """
        Get ISO format timestamp.

        Returns:
            ISO 8601 formatted timestamp
        """
        return datetime.now(self.timezone).isoformat()

    def get_simple_date(self) -> str:
        """
        Get simple date string (YYYY-MM-DD).

        Returns:
            Date in YYYY-MM-DD format
        """
        return datetime.now(self.timezone).strftime('%Y-%m-%d')

    def format_relative(self, date_str: str) -> str:
        """
        Format how old a date is (e.g., '3 days ago').

        Args:
            date_str: ISO format date string

        Returns:
            Relative time string
        """
        try:
            # Parse the date
            if 'T' in date_str:
                # ISO format with time
                then = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                # Just date
                then = datetime.strptime(date_str, '%Y-%m-%d')
                # Make timezone-aware with UTC
                then = then.replace(tzinfo=timezone.utc)

            # Get current time in UTC for comparison
            now = datetime.now(timezone.utc)

            # Calculate delta
            delta = now - then
            days = delta.days

            # Format relative
            if days == 0:
                return "today"
            elif days == 1:
                return "yesterday"
            elif days < 7:
                return f"{days} days ago"
            elif days < 30:
                weeks = days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            elif days < 365:
                months = days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
            else:
                years = days // 365
                return f"{years} year{'s' if years > 1 else ''} ago"

        except Exception as e:
            print(f"⚠️  Could not parse date '{date_str}': {e}")
            return date_str

    def is_recent(self, date_str: str, days_threshold: int = 90) -> bool:
        """
        Check if a date is recent (within threshold).

        Args:
            date_str: ISO format date string
            days_threshold: Number of days to consider recent

        Returns:
            True if date is within threshold
        """
        try:
            if 'T' in date_str:
                then = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                then = datetime.strptime(date_str, '%Y-%m-%d')
                then = then.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            delta = now - then

            return delta.days <= days_threshold

        except Exception:
            return False

    def get_week_context(self) -> str:
        """
        Get context about current week.

        Returns:
            String describing week number and position
        """
        now = datetime.now(self.timezone)
        week_number = now.isocalendar()[1]
        day_of_week = now.weekday()  # 0 = Monday

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_name = days[day_of_week]

        return f"Week {week_number} of {now.year}, currently {day_name}"
