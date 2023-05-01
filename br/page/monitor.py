import json
import os.path
import pathlib
import time
import uuid
from threading import Event, Thread, Lock

from hbutils.random import random_sha1_with_timestamp
from selenium.common import NoSuchWindowException
from selenium.webdriver.remote.webdriver import WebDriver

from ..utils import capture_screen

_LISTENER_JS = pathlib.Path(os.path.normpath(os.path.join(__file__, '..', 'listener.js'))).read_text()


def add_monitor(driver: WebDriver):
    driver.execute_script(_LISTENER_JS)


def read_records(driver: WebDriver):
    return driver.execute_script('return document.loadRecords();')


class WebDriverMonitor:
    def __init__(self, driver: WebDriver, save_dir: str, interval: float = 0.2):
        self.driver = driver
        self.save_dir = save_dir
        self.interval = interval

        self._last_driver_url = None
        self._start_signal = Event()
        self._stop_signal = Event()
        self._page_records = []

        self._t_page_event = Thread(target=self._page_event_monitor)
        self._t_system_screenshot = Thread(target=self._system_screenshot)
        self._t_result_save = Thread(target=self._result_save)

        self._lock = Lock()

    def _page_event_monitor(self):
        _last_time = time.time()
        while not self._stop_signal.is_set():

            try:
                if self.driver.current_url != self._last_driver_url:
                    self._page_records.append({
                        'event': 'url_change',
                        'time': time.time(),
                        'uuid': str(uuid.uuid4()),
                        'last_url': self._last_driver_url,
                        'new_url': self.driver.current_url,
                    })
                    self._last_driver_url = self.driver.current_url
                    add_monitor(self.driver)
                self._page_records.extend(read_records(self.driver))
            except NoSuchWindowException:
                self._stop_signal.set()
                break

            _last_time += self.interval
            _duration = _last_time - time.time()
            if _duration > 0:
                time.sleep(_duration)

    def _system_screenshot(self):
        _last_time = time.time()
        while not self._stop_signal.is_set():
            name = f'screenshot_{random_sha1_with_timestamp()}.png'
            dirname = os.path.join(self.save_dir, 'screenshots')
            os.makedirs(dirname, exist_ok=True)
            filename = os.path.join(dirname, name)
            image, timestamp = capture_screen()
            image.save(filename)
            self._page_records.append({
                'event': 'screenshot',
                'time': time.time(),
                'uuid': str(uuid.uuid4()),
                'image': name,
            })
            print('sc', time.time())

            _last_time += self.interval
            _duration = _last_time - time.time()
            if _duration > 0:
                time.sleep(_duration)

    def _result_save(self):
        self._stop_signal.wait()
        self._t_page_event.join()
        self._t_system_screenshot.join()

        items = [item for _, item in sorted(enumerate(self._page_records), key=lambda x: (x[1]['time'], x[0]))]
        with open(os.path.join(self.save_dir, 'record.json'), 'w') as f:
            json.dump(items, f, indent=4)

    def _join(self):
        self._stop_signal.wait()
        self._t_system_screenshot.join()
        self._t_page_event.join()
        self._t_result_save.join()

    def start(self):
        with self._lock:
            os.makedirs(self.save_dir, exist_ok=True)
            self._t_system_screenshot.start()
            self._t_page_event.start()
            self._t_result_save.start()

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
