#!/usr/bin/env python3

"""
Takes as input a JSON file containing description of weekly events.
Outputs a timetable in HTML.
"""

import argparse
import json
from os.path import dirname, realpath
from os.path import join as pjoin

from jinja2 import Template


PUBLIC_KEYS = ['name', 'description']
PRIVATE_KEYS = ['venue']
DAYS = ["Mon", "Tues", "Wed", "Thurs", "Fri", "Sat", "Sun"]
DAY_TO_INDEX = {day: i for (i, day) in enumerate(DAYS)}
CURDIR = dirname(realpath(__file__))


def getPrivateKey(k):
    return 'private' + k.capitalize()


def getTimeFrac(timeStr, minHour, maxHour):
    h = int(timeStr[:2])
    m = int(timeStr[3:5])
    return ((h - minHour) * 60 + m) / (60 * (maxHour - minHour))


def readInput(ipath, isPrivate):
    with open(ipath) as fp:
        rawEvents = json.load(fp)
    events = []
    for rawEvent in rawEvents:
        if 'hidden' in rawEvent:
            continue
        eventTemplate = {}
        keys = PUBLIC_KEYS + PRIVATE_KEYS if isPrivate else PUBLIC_KEYS
        for k in keys:
            if k in rawEvent:
                eventTemplate[k] = rawEvent[k]
        if isPrivate:
            for k in PUBLIC_KEYS + PRIVATE_KEYS:
                privK = getPrivateKey(k)
                if privK in rawEvent:
                    eventTemplate[k] = rawEvent[privK]
        if 'days' in rawEvent:
            days = rawEvent['days']
        elif 'day' in rawEvent:
            days = [rawEvent['day']]
        else:
            raise ValueError("event doesn't have day(s)")
        if 'times' in rawEvent:
            times = rawEvent['times']
        elif 'time' in rawEvent:
            times = [rawEvent['time']]
        else:
            raise ValueError("event doesn't have time(s)")
        for day in days:
            dayIndex = DAY_TO_INDEX[day]
            for time in times:
                assert len(time) == 2 and isinstance(time[0], str) and isinstance(time[1], str)
                assert time[0] <= time[1]
                event = eventTemplate.copy()
                event['dayIndex'] = dayIndex
                event['beginTime'] = time[0]
                event['endTime'] = time[1]
                events.append(event)
    return events


def getRenderContext(events):
    dayIndices = [event['dayIndex'] for event in events]
    minDayIndex = min(dayIndices)
    maxDayIndex = max(dayIndices)
    dayLabels = DAYS[minDayIndex: maxDayIndex+1]

    def getEndHour(timeStr):
        h = int(timeStr[:2])
        return h + 1 if timeStr[3:5] != '00' else h

    minHour = min([int(event['beginTime'][:2]) for event in events])
    maxHour = max([getEndHour(event['endTime']) for event in events])

    eventsByDay = [[] for dl in dayLabels]
    for event in events:
        event['beginFrac'] = getTimeFrac(event['beginTime'], minHour, maxHour)
        event['lenFrac'] = getTimeFrac(event['endTime'], minHour, maxHour) - event['beginFrac']
        di = event['dayIndex'] - minDayIndex
        del event['dayIndex']
        eventsByDay[di].append(event)
    for (di, dl) in enumerate(dayLabels):
        eventsByDay[di].sort(key=(lambda event: event['beginFrac']))

    context = {
        'events': eventsByDay,
        'dayLabels': dayLabels,
        'minHour': minHour,
        'maxHour': maxHour,
    }
    return context


def writeOutput(context, opath):
    with open(pjoin(CURDIR, 'style.css')) as fp:
        context['style'] = fp.read()
    with open(pjoin(CURDIR, 'template.html.jinja2')) as fp:
        template = Template(fp.read(), trim_blocks=True)
    page = template.render(context)
    with open(opath, 'w') as fp:
        fp.write(page)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ipath', help='Path to input JSON file.')
    parser.add_argument('--private', action='store_true', default=False,
        help='Run in private mode.')
    parser.add_argument('-o', '--output', required=True, help='Path to output HTML file.')
    args = parser.parse_args()

    events = readInput(args.ipath, args.private)
    context = getRenderContext(events)
    writeOutput(context, args.output)


if __name__ == '__main__':
    main()
