import browsers
from selenium.webdriver import Chrome
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.dispatch import get_browser_manager


def get_browser_driver() -> WebDriver:
    browser = browsers.get('chrome')
    if not browser:
        raise ModuleNotFoundError('Chrome browser not found.')

    bm = get_browser_manager('chrome')
    chrome = Chrome(bm.driver_executable)
    return chrome
