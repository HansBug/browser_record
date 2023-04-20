# browser_record

```shell
pip install -r requirements.txt
```

Simplest demo (chrome browser required.)

```python
import time

from br.page import create_monitor_thread
from br.utils import get_browser_driver

if __name__ == '__main__':
    chrome = get_browser_driver()

    _start, _stop = create_monitor_thread(chrome, save_dir='test_records/1')
    chrome.get('https://www.baidu.com')
    _start()  # start watch on browser

    time.sleep(10)

    _stop()  # stop watching and save to the save_dir
    chrome.close()

```
