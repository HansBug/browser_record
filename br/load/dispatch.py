import json

from .events import CursorTracker, ViewAreaTracker, ScrollTracker, ResizeTracker
from .vision import VisionTracker, VisibleTracker


class BrowserRecord:
    def __init__(self, data):
        self.data = data
        self._events = self.data['events']

        view_area = ViewAreaTracker(
            ScrollTracker([
                ((item['scroll_x'], item['scroll_y']), item['time'])
                for item in self._events if item['event'] == 'scroll'
            ]), ResizeTracker([
                ((item['view_width'], item['view_height']), item['time'])
                for item in self._events if item['event'] == 'resize'
            ])
        )

        self.cursor = CursorTracker([
            ((item['x'], item['y']), item['time'])
            for item in self._events if item['event'] == 'mousemove'
        ])

        full_page = VisionTracker(self.data['page_vision'])
        self.page_vision = VisibleTracker(full_page, view_area)

        self.sys_vision = VisionTracker(self.data['system_vision'])

    @property
    def start_time(self) -> float:
        return self.data['start_time']

    @property
    def end_time(self) -> float:
        return self.data['end_time']

    @property
    def events(self):
        return list(self._events)

    @classmethod
    def load_from_json(cls, file):
        with open(file, 'r') as f:
            return cls(json.load(f))
