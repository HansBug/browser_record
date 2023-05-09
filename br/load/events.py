from typing import Tuple, List, Optional

from .base import _TimeBasedSequence, _SequenceCombine


class CursorTracker(_TimeBasedSequence):
    def __init__(self, positions: List[Tuple[Tuple[float, float], float]]):
        _TimeBasedSequence.__init__(self, positions)

    def position(self, time: float) -> Optional[Tuple[float, float]]:
        return self._get_state_on_time(time)


class RelCursorTracker(_SequenceCombine):
    def __init__(self, cursor: CursorTracker, view_area: 'ViewAreaTracker'):
        self.cursor = cursor
        self.view_area = view_area
        _SequenceCombine.__init__(self, self.cursor, self.view_area)

    def position(self, time: float) -> Optional[Tuple[float, float]]:
        _index = self.cursor._get_index_before_time(time)
        print(_index)
        if _index is not None:
            (x, y), _cursor_time = self.cursor.items[_index]
            print(x, y, _cursor_time)
            area = self.view_area.area(_cursor_time)
            if area is not None:
                x0, y0, _, _ = area
                print(x0, y0)
                return x - x0, y - y0

        return None


class ScrollTracker(_TimeBasedSequence):
    def __init__(self, positions: List[Tuple[Tuple[float, float], float]]):
        _TimeBasedSequence.__init__(self, positions)

    def position(self, time: float) -> Optional[Tuple[float, float]]:
        return self._get_state_on_time(time)


class ResizeTracker(_TimeBasedSequence):
    def __init__(self, sizes: List[Tuple[Tuple[float, float], float]]):
        _TimeBasedSequence.__init__(self, sizes)

    def size(self, time: float) -> Optional[Tuple[float, float]]:
        return self._get_state_on_time(time)


class ViewAreaTracker(_SequenceCombine):
    def __init__(self, scroll: ScrollTracker, resize: ResizeTracker):
        self.scroll = scroll
        self.resize = resize
        _SequenceCombine.__init__(self, self.scroll, self.resize)

    def area(self, time: float) -> Optional[Tuple[float, float, float, float]]:
        position = self.scroll.position(time)
        size = self.resize.size(time)
        if position and size:
            (x, y), (width, height) = position, size
            return x, y, width, height
        else:
            return None
