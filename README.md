# browser_record

```shell
pip install -r requirements.txt
```

Simplest demo (chrome browser required.)

```python
import time

from br.page import add_monitor, read_records
from br.utils import get_browser_driver

chrome = get_browser_driver()

chrome.get('https://www.baidu.com')
add_monitor(chrome)

time.sleep(10)

print(read_records(chrome))

chrome.close()

```
