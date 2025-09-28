"""
Main module
"""

from datetime import datetime
from src.event import Event
from src.executor import execute

if __name__ == "__main__":
    e = Event(
        id=1,
        name="Test Event",
        description="This is a test event",
        origin="https://github.com/lyubolp/tmp-2",
        destination="https://github.com/lyubolp/tmp-1",
        date=datetime.now(),
        patterns=[("baz.txt", "temp/baz-2.txt"), ("*.py", None)],
    )

    execute(e)
