import json
import os.path
import pathlib
import time
import uuid
from threading import Event, Thread

from hbutils.random import random_sha1_with_timestamp
from selenium.webdriver.remote.webdriver import WebDriver

from ..utils import capture_screen

_LISTENER_JS = pathlib.Path(os.path.normpath(os.path.join(__file__, '..', 'listener.js'))).read_text()


def add_monitor(driver: WebDriver):
    driver.execute_script(_LISTENER_JS)


def read_records(driver: WebDriver):
    return driver.execute_script('return document.loadRecords();')


def create_monitor_thread(driver: WebDriver, save_dir: str, interval: float = 0.2):
    last_driver_url = None
    stop_signal = Event()
    page_records = []

    def _thread_func():
        nonlocal last_driver_url
        _last_time = time.time()
        while not stop_signal.is_set():
            if driver.current_url != last_driver_url:
                page_records.append({
                    'event': 'url_change',
                    'time': time.time(),
                    'uuid': str(uuid.uuid4()),
                    'last_url': last_driver_url,
                    'new_url': driver.current_url,
                })
                last_driver_url = driver.current_url
                add_monitor(driver)

            page_records.extend(read_records(driver))
            _last_time += interval
            _duration = _last_time - time.time()
            if _duration > 0:
                time.sleep(_duration)

    def _capture_func():
        _last_time = time.time()
        while not stop_signal.is_set():
            name = f'screenshot_{random_sha1_with_timestamp()}.png'
            dirname = os.path.join(save_dir, 'screenshots')
            os.makedirs(dirname, exist_ok=True)
            filename = os.path.join(dirname, name)
            image, timestamp = capture_screen()
            image.save(filename)
            page_records.append({
                'event': 'screenshot',
                'time': time.time(),
                'uuid': str(uuid.uuid4()),
                'image': name,
            })

            _last_time += interval
            _duration = _last_time - time.time()
            if _duration > 0:
                time.sleep(_duration)

    t1 = Thread(target=_thread_func)
    t2 = Thread(target=_capture_func)

    def _start():
        os.makedirs(save_dir, exist_ok=True)
        t1.start()
        t2.start()

    def _stop():
        stop_signal.set()
        t1.join()
        t2.join()

        items = [item for _, item in sorted(enumerate(page_records), key=lambda x: (x[1]['time'], x[0]))]
        with open(os.path.join(save_dir, 'record.json'), 'w') as f:
            json.dump(items, f, indent=4)

    return _start, _stop
