import json
import os.path
import pathlib
import time
import uuid
from queue import Queue, Empty
from threading import Event, Thread, Lock

from hbutils.string import env_template
from selenium.common import NoSuchWindowException
from selenium.webdriver.remote.webdriver import WebDriver

from .vision import VisionRecorder, _base64_url_to_image
from ..utils import capture_screen

_LISTENER_JS = pathlib.Path(os.path.normpath(os.path.join(__file__, '..', 'listener.js'))).read_text()
_HTML2CANVAS_JS = pathlib.Path(os.path.normpath(os.path.join(__file__, '..', 'html2canvas.js'))).read_text()


def add_monitor(driver: WebDriver):
    driver.execute_script(_LISTENER_JS)


def read_event_records(driver: WebDriver):
    return driver.execute_script('return document.loadRecords();') or []


def add_html2canvas(driver: WebDriver, interval_ms: int = 200):
    driver.execute_script(env_template(_HTML2CANVAS_JS, {'interval_ms': interval_ms}, safe=True))


def read_screenshot_records(driver: WebDriver):
    return driver.execute_script('return document.loadScreenshotRecords();') or []


class WebDriverMonitor:
    def __init__(self, driver: WebDriver, save_as: str, event_interval: float = 0.2,
                 system_view_interval: float = 1.0):
        self.driver = driver
        self.save_as = save_as
        self.event_interval = event_interval
        self.system_view_interval = system_view_interval

        self._start_signal = Event()
        self._stop_signal = Event()
        self._start_time = None
        self._end_time = None
        self._page_event_records = []

        self._page_vision_queue = Queue()
        self._page_vision = VisionRecorder()
        self._system_vision = VisionRecorder()

        self._t_page_event = Thread(target=self._page_event_monitor)
        self._t_page_vision_maintain = Thread(target=self._page_vision_maintain)
        self._t_system_screenshot = Thread(target=self._system_screenshot)
        self._t_result_save = Thread(target=self._result_save)

        self._lock = Lock()

    def _page_vision_maintain(self):
        while not self._stop_signal.is_set() or not self._page_vision_queue.empty():
            try:
                item = self._page_vision_queue.get(block=True, timeout=self.event_interval)
            except Empty:
                continue

            timestamp, raw_data = item['time'], item['raw']
            self._page_vision.append(_base64_url_to_image(raw_data), timestamp)

    def _page_event_monitor(self):
        _last_time = time.time()
        _last_driver_url = None
        while not self._stop_signal.is_set():
            try:
                if self.driver.current_url != _last_driver_url:
                    self._page_event_records.append({
                        'event': 'url_change',
                        'time': time.time(),
                        'uuid': str(uuid.uuid4()),
                        'last_url': _last_driver_url,
                        'new_url': self.driver.current_url,
                    })
                    _last_driver_url = self.driver.current_url
                    add_monitor(self.driver)
                    add_html2canvas(self.driver, int(self.event_interval * 1000))

                self._page_event_records.extend(read_event_records(self.driver))
                for item in read_screenshot_records(self.driver):
                    self._page_vision_queue.put(item)

            except NoSuchWindowException:
                self._stop_signal.set()
                break

            _last_time += self.event_interval
            _duration = _last_time - time.time()
            if _duration > 0:
                time.sleep(_duration)

    def _system_screenshot(self):
        _last_time = time.time()
        while not self._stop_signal.is_set():
            image, timestamp = capture_screen()
            self._system_vision.append(image, timestamp)

            _last_time += self.system_view_interval
            _duration = _last_time - time.time()
            if _duration > 0:
                time.sleep(_duration)

    def _wait_for_watching_end(self):
        self._stop_signal.wait()
        self._end_time = time.time()
        self._t_page_event.join()
        self._t_page_vision_maintain.join()
        self._t_system_screenshot.join()

    def _result_save(self):
        self._wait_for_watching_end()
        events = [item for _, item in sorted(enumerate(self._page_event_records), key=lambda x: (x[1]['time'], x[0]))]
        save_dir = os.path.dirname(self.save_as)
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        with open(self.save_as, 'w') as f:
            json.dump({
                'start_time': self._start_time,
                'end_time': self._end_time,
                'events': events,
                'page_vision': self._page_vision.to_json(),
                'system_vision': self._system_vision.to_json(),
            }, f, indent=4)

    def _join(self):
        self._stop_signal.wait()
        self._t_system_screenshot.join()
        self._t_page_event.join()
        self._t_page_vision_maintain.join()
        self._t_result_save.join()

    def start(self):
        with self._lock:
            self._t_system_screenshot.start()
            self._t_page_vision_maintain.start()
            self._t_page_event.start()
            self._t_result_save.start()
            self._start_time = time.time()

    def stop(self):
        with self._lock:
            self._stop_signal.set()
            self._join()

    def join(self):
        with self._lock:
            self._join()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._join()
