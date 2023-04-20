import os.path
import pathlib

from selenium.webdriver.remote.webdriver import WebDriver

_LISTENER_JS = pathlib.Path(os.path.normpath(os.path.join(__file__, '..', 'listener.js'))).read_text()


def add_monitor(driver: WebDriver):
    driver.execute_script(_LISTENER_JS)


def read_records(driver: WebDriver):
    return driver.execute_script('return document.loadRecords();')
