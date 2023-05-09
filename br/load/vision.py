import io
import zlib

import numpy as np
from PIL import Image
from hbutils.encoding import base64_decode

from .base import _TimeBasedSequence, _SequenceCombine
from .events import ViewAreaTracker
from ..page.vision import VisionItemType


def _b64_to_array(b64_text: str):
    b64_binary = zlib.decompress(base64_decode(b64_text))
    with io.BytesIO(b64_binary) as bio:
        return np.load(bio, allow_pickle=True)


class VisionTracker(_TimeBasedSequence):
    def __init__(self, data):
        _TimeBasedSequence.__init__(self, [
            ((VisionItemType.loads(item['type']), item['data']), item['timestamp']) for item in data
        ])

    def vision(self, time: float):
        index = self._get_index_before_time(time)
        if index is None:
            return None

        new_index = index
        while new_index > 0:
            (type_, _), _ = self.items[new_index]
            if type_ == VisionItemType.NEW_FRAME:
                break
            new_index -= 1

        (type_, b64_text), _ = self.items[new_index]
        assert type_ == VisionItemType.NEW_FRAME
        image_arr = _b64_to_array(b64_text)

        for i in range(new_index + 1, index + 1):
            (type_, b64_text), _ = self.items[i]
            assert type_ == VisionItemType.DIFF_FRAME
            diff_arr = _b64_to_array(b64_text)
            xs, ys = diff_arr[0], diff_arr[1]
            image_arr[0, xs, ys] = ((diff_arr[2] >> 16) & 0xff).astype(np.uint8)
            image_arr[1, xs, ys] = ((diff_arr[2] >> 8) & 0xff).astype(np.uint8)
            image_arr[2, xs, ys] = ((diff_arr[2] >> 0) & 0xff).astype(np.uint8)

        return Image.fromarray(image_arr.transpose((1, 2, 0)), mode='LAB').convert('RGB')


class VisibleTracker(_SequenceCombine):
    def __init__(self, vision: VisionTracker, view_area: ViewAreaTracker):
        self._vision = vision
        self._view_area = view_area
        _SequenceCombine.__init__(self, self._vision, self._view_area)

    def vision(self, time: float):
        full_image = self._vision.vision(time)
        area = self._view_area.area(time)
        if full_image and area:
            x, y, width, height = area
            return full_image.crop((x, y, x + width, y + height))
