# Timetabler

`timetabler.py` takes as input a JSON file containing a list of weekly events
and outputs a timetable in HTML format.
It is supposed to look similar to Google calendar's 'Day' format.

Example invocations:

    python3 timetabler.py example.json -o output.html
    python3 timetabler.py example.json --private -o output.html
