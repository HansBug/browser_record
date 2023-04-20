import browsers
from selenium.webdriver import Chrome
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.dispatch import get_browser_manager

_ORDER = ['chrome', 'firefox', 'msedge', 'opera']


def get_browser_driver() -> WebDriver:
    for b in _ORDER:
        browser = browsers.get(b)
        if not browser:
            continue

        bm = get_browser_manager(b)
        chrome = Chrome(bm.driver_executable)
        return chrome
    else:
        raise ModuleNotFoundError('No browser detected!.')
