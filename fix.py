from __future__ import annotations
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import urllib.request

SRC_URL = "https://uisdxp.sis.jhu.edu/api/course/calendar/acecbc560d094b9fbb80ae7180e10027"
OUT = Path("docs/calendar.ics")

NY = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

UTC_LINE = re.compile(r"^(DTSTART|DTEND)(?:;[^:]*)?:([0-9]{8}T[0-9]{6})Z\s*$", re.MULTILINE)

VTIMEZONE = """BEGIN:VTIMEZONE
TZID:America/New_York
X-LIC-LOCATION:America/New_York
BEGIN:DAYLIGHT
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
END:VTIMEZONE
"""

def fetch(url: str) -> str:
    with urllib.request.urlopen(url) as r:
        return r.read().decode("utf-8")

def convert(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        dt_utc = datetime.strptime(m.group(2), "%Y%m%dT%H%M%S").replace(tzinfo=UTC)
        dt_ny = dt_utc.astimezone(NY)
        return f"{key};TZID=America/New_York:{dt_ny.strftime('%Y%m%dT%H%M%S')}"

    out = UTC_LINE.sub(repl, text)

    if "X-WR-TIMEZONE" not in out:
        out = out.replace("BEGIN:VCALENDAR", "BEGIN:VCALENDAR\nX-WR-TIMEZONE:America/New_York", 1)

    if "BEGIN:VTIMEZONE" not in out:
        i = out.find("BEGIN:VEVENT")
        if i != -1:
            out = out[:i] + VTIMEZONE + "\n" + out[i:]
        else:
            out += "\n" + VTIMEZONE + "\n"

    return out

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(convert(fetch(SRC_URL)), encoding="utf-8")

if __name__ == "__main__":
    main()
