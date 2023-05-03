function getTimestamp() {
    let currentDate = new Date();
    let currentTimestamp = currentDate.getTime();
    return currentTimestamp / 1000.0;
}

function generateUUID() {
    let d = new Date().getTime();

    if (typeof performance !== 'undefined' && typeof performance.now === 'function') {
        d += performance.now(); // 使用性能API，增加微秒级时间戳
    }

    const uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = (d + Math.random() * 16) % 16 | 0;
        d = Math.floor(d / 16);
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });

    return uuid;
}


function deepcopy(v) {
    return JSON.parse(JSON.stringify(v))
}

function addMonitor() {
    if (document.isMonitored) {
        return false;
    }

    let arr = []

    function appendRecord(record) {
        let full_record = Object.assign({
            time: getTimestamp(), uuid: generateUUID(),
        }, record)
        arr.push(full_record)
    }

    document.addEventListener('click', function (event) {
        appendRecord({
            event: 'click', x: event.clientX, y: event.clientY, text: event.target.innerText,
        });
    });
    document.addEventListener('dblclick', function (event) {
        appendRecord({
            event: 'dblclick', x: event.clientX, y: event.clientY, text: event.target.innerText,
        });
    });
    document.addEventListener('mousemove', function (event) {
        appendRecord({
            event: 'mousemove', x: event.clientX, y: event.clientY,
        });
    });
    document.addEventListener('dragstart', function (event) {
        appendRecord({
            event: 'dragstart', x: event.clientX, y: event.clientY,
        })
    })
    document.addEventListener('drag', function (event) {
        appendRecord({
            event: 'drag', x: event.clientX, y: event.clientY,
        })
    })
    document.addEventListener('dragend', function (event) {
        appendRecord({
            event: 'dragend', x: event.clientX, y: event.clientY,
        })
    })
    document.addEventListener('keypress', function (event) {
        appendRecord({
            event: 'keypress',
            key: event.key,
            code: event.code,
            shift: event.shiftKey,
            alt: event.altKey,
            ctrl: event.ctrlKey,
        })
    })

    function _recordScrollInfo() {
        appendRecord({
            event: 'scroll',
            scroll_x: window.pageXOffset || document.documentElement.scrollLeft || document.body.scrollLeft,
            scroll_y: window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop,
        });
    }

    function _recordViewInfo() {
        appendRecord({
            event: 'resize',
            view_height: window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight,
            view_width: window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth,
        });
    }

    _recordScrollInfo()
    _recordViewInfo()

    window.addEventListener('scroll', function (event) {
        _recordScrollInfo()
    });
    window.addEventListener('resize', function (event) {
        _recordViewInfo()
    })

    document.loadRecords = function () {
        let retval = deepcopy(arr);
        arr.splice(0, arr.length);
        return retval;
    }
    document.isMonitored = true;

    console.log('Monitor added.')
    return true;
}

addMonitor();
