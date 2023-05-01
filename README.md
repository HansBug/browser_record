# browser_record

```shell
pip install -r requirements.txt
```

Simplest demo (chrome browser required.)

```python
from br.page import WebDriverMonitor
from br.utils import get_browser_driver

if __name__ == '__main__':
    chrome = get_browser_driver()

    with WebDriverMonitor(chrome, save_dir='test_records/2x') as monitor:
        chrome.get('https://www.baidu.com')
        monitor.start()

        # wait until use close the window

    chrome.quit()

```
