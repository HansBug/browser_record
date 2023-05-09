import io
import os
import zlib
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional

import numpy as np
from PIL import Image
from hbutils.encoding import base64_encode, base64_decode
from hbutils.string import truncate
from hbutils.system import TemporaryDirectory


class VisionItemType(IntEnum):
    NEW_FRAME = 0x1
    DIFF_FRAME = 0x2

    @classmethod
    def loads(cls, obj):
        if isinstance(obj, cls):
            return obj
        elif isinstance(obj, str):
            return cls.__members__[obj.upper()]
        else:
            raise TypeError(f'Unknown vision type - {obj!r}.')


def _numpy_to_base64(arr: np.ndarray):
    with io.BytesIO() as bio:
        np.save(bio, arr, allow_pickle=True)
        return base64_encode(zlib.compress(bio.getvalue()))


@dataclass
class VisionItem:
    type: VisionItemType
    timestamp: float
    data: np.ndarray

    def to_json(self):
        return {
            'type': self.type.name.lower(),
            'timestamp': self.timestamp,
            'data': _numpy_to_base64(self.data),
        }


_BASE64_URL_PREFIX = 'data:image/png;base64,'


def _base64_url_to_image(url: str):
    assert url.startswith(_BASE64_URL_PREFIX), \
        f'Url should start with {_BASE64_URL_PREFIX!r}, ' \
        f'but {truncate(url, show_length=True, tail_length=15, width=120)!r} found'

    with TemporaryDirectory() as td:
        filename = os.path.join(td, 'file.png')
        with open(filename, 'wb') as f:
            f.write(base64_decode(url[len(_BASE64_URL_PREFIX):]))

        image = Image.open(filename)
        image.load()
        return image


class VisionRecorder:
    def __init__(self, max_diff_frames: int = 50, min_deflation: float = 0.1, pixel_diff_threshold: float = 0.05):
        self._records: List[VisionItem] = []
        self._last_view: Optional[Image.Image] = None
        self._last_new_frame: int = -1

        self.max_diff_frames = max_diff_frames
        self.min_deflation = min_deflation
        self.pixel_diff_threshold = pixel_diff_threshold

    def _append_new_frame(self, view: Image.Image, timestamp: float):
        self._last_view = view
        data = np.array(view.convert('LAB')).transpose((2, 0, 1))
        self._last_new_frame = len(self._records)
        self._records.append(VisionItem(VisionItemType.NEW_FRAME, timestamp, data))

    def _try_append_diff_frame(self, view: Image.Image, timestamp: float):
        lab1 = np.array(self._last_view.convert('LAB'))
        lab2 = np.array(view.convert('LAB'))

        f_lab1 = lab1.astype(float) / 255.0
        f_lab2 = lab2.astype(float) / 255.0

        i_lab2 = lab2.astype(np.uint32).transpose((2, 0, 1))
        i_lab2 = (i_lab2[0] << 16) | (i_lab2[1] << 8) | i_lab2[2]

        distances = ((f_lab1 - f_lab2) ** 2).sum(axis=2) ** 0.5
        xs, ys = np.where(distances > self.pixel_diff_threshold)

        diff_data = np.stack([xs.astype(np.uint32), ys.astype(np.uint32), i_lab2[xs, ys]])
        deflation = (lab2.nbytes - diff_data.nbytes) / lab2.nbytes

        if deflation < self.min_deflation:  # two low, just create a new frame
            self._append_new_frame(view, timestamp)
        else:  # create a diff frame
            self._last_view = view
            self._records.append(VisionItem(VisionItemType.DIFF_FRAME, timestamp, diff_data))

    def append(self, view: Image.Image, timestamp: float):
        if self._records and self._records[-1].timestamp > timestamp:
            raise ValueError('Timestamp should be monotonically increasing, '
                             f'but it was detected that the previous timestamp was {self._records[-1].timestamp!r}, '
                             f'while this one is {timestamp}.')

        if self._last_view is None or self._last_view.size != view.size or \
                (len(self._records) - self._last_new_frame) > self.max_diff_frames:
            self._append_new_frame(view, timestamp)
        else:
            self._try_append_diff_frame(view, timestamp)

    def append_base64_url(self, url: str, timestamp: float):
        self.append(_base64_url_to_image(url), timestamp)

    def to_json(self):
        return [item.to_json() for item in self._records]
