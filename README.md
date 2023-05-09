# browser_record

```shell
pip install -r requirements.txt
```

Simplest demo (chrome browser required.) of recording the operations

```python
import os

from br.page import WebDriverMonitor
from br.utils import get_browser_driver

if __name__ == '__main__':
    # use out mirror site, or huggingface.co will be used
    os.environ['DRIVER_SITE'] = 'https://opendilab.net/download/webdrivers/'

    chrome = get_browser_driver()

    with WebDriverMonitor(chrome, save_as='test_records/2x.json') as monitor:
        chrome.get('https://www.baidu.com')
        monitor.start()

        # wait until use close the window

    chrome.quit()

```

and then query the state

```python
import matplotlib.pyplot as plt

from br.load import BrowserRecord

if __name__ == '__main__':
    record = BrowserRecord.load_from_json('test_records/2x.json')

    # select a time point, which should be in [record.start_time, record.end_time]
    time = record.start_time + 7.9

    # plot vision in browser at this time
    plt.imshow(record.page_vision.vision(time))

    # plot cursor position at this time
    x, y = record.cursor.position(time)
    plt.scatter([x], [y], color='green', marker='*', edgecolor='white', s=150)

    # plot vision in system at this time
    # plt.imshow(record.sys_vision.vision(time))

    plt.show()

```