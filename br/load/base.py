from bisect import bisect_right
from typing import List, Tuple, Any, Union

from hbutils.string import plural_word


class _TimeBasedSequence:
    def __init__(self, items: List[Tuple[Any, float]]):
        self.items = [(obj, time_) for _, (obj, time_) in sorted(enumerate(items), key=lambda x: (x[1][1], x[0]))]
        self.times = [time_ for _, time_ in self.items]

    @property
    def start_time(self) -> float:
        return self.times[0]

    @property
    def end_time(self) -> float:
        return self.times[-1]

    def _get_index_before_time(self, time_: float) -> int:
        i = bisect_right(self.times, time_)
        return i - 1 if i else None

    def _get_state_on_time(self, time_: float):
        i = self._get_index_before_time(time_)
        if i is not None:
            obj, _ = self.items[i]
            return obj
        else:
            return None

    def __repr__(self):
        return f'<{self.__class__.__name__} [{self.start_time}, {self.end_time}], ' \
               f'{self.end_time - self.start_time:.3f} seconds, ' \
               f'{plural_word(len(self.times), "item")}>'


class _SequenceCombine:
    def __init__(self, *seqs: Union[_TimeBasedSequence, '_SequenceCombine']):
        self._seqs = seqs

    @property
    def start_time(self) -> float:
        return max(map(lambda x: x.start_time, self._seqs))

    @property
    def end_time(self) -> float:
        return max(map(lambda x: x.end_time, self._seqs))

    def __repr__(self):
        return f'<{self.__class__.__name__} [{self.start_time}, {self.end_time}], ' \
               f'{self.end_time - self.start_time:.3f} seconds>'
