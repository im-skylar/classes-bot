import datetime

# If it turns out this is not needed or we'll need more granularity (ie) quarter-hourly, we can define classes as multi-bit bitmasks and then match by student_times & class_times == class_times


class TimeTable():
    def __init__(self, tz: datetime.timezone) -> None:
        self._rep = 0
        self.tz = tz

    @property
    def int_representation(self) -> int:
        return self._rep

    
    def append_time(self, starth: int, endh: int, dow: int, enddow: int | None = None) -> None:
        """
        Add a time to a timetable.

        Args:
            starth: Starting hour, with 0 = 00:00 AM, 12 = 12:00 PM, 13 = 01:00 PM.
            endh: Ending hour, inclusive
            dow: Day of week, starting with 0 for Monday.
            enddow: Last day of week to add. Will assume only dow if left None. Can be before dow.
        """

        if enddow is None:
            enddow = dow

        if enddow < dow:
            enddow += 7

        # This could be improved by more bit-magic but honestly who cares
        for d in range(dow, enddow+1):
            for h in range(starth, endh+1):
                self._rep |= 1 << (h + d * 24)




    
