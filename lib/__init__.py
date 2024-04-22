#!/usr/bin/env python3
# coding: utf-8

import multiprocessing.pool
import http.cookiejar
import html
import urllib
import time
import random

# Shared variables
CJ = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CJ))
T = str(int(time.time()))
H = html

from lib.logger import LOG
from lib.logger import ERROR
from lib.logger import LOG_TIME
from lib.logger import LOG_TIME_END
from lib.textProcessor import content_handle


# Shared crawler utils
def parallel_handle(
    returnable_func=lambda x: x, input_array=[], worker_num=6, timeout=3
):
    multiprocessing.freeze_support()
    pool = multiprocessing.Pool(worker_num)
    results = []
    for i in range(0, len(input_array)):
        result = pool.apply_async(returnable_func, args=(input_array[i],))
        results.append(result)
    pool.close()
    pool.join()
    return [result.get(timeout=timeout) for result in results]


def getContent(url, TXTENCODE=None, max_tries=10, sleep_time=0.001):
    counter = 0
    buf = ""
    while counter <= max_tries:
        try:
            time.sleep(sleep_time)
            LOG(url, "[Start]", "(tried count: %s, url: %s)" % (counter, url))
            version = str(int(random.random() * 10 + 70))
            req = urllib.request.Request(
                url,
                data=None,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/%s.0.1916.47 Safari/537.36"
                    % version
                },
            )
            fd = OPENER.open(req, timeout=7)
            if TXTENCODE == None:
                buf = fd.read()
            else:
                buf = H.unescape(fd.read().decode(TXTENCODE, "ignore"))
            LOG(url, "[Done]", "(tried count: %s, url: %s, buf: %s)" % (counter, url, len(buf)))
            break
        except Exception as e:
            LOG(e, url, counter)
            counter += 1
            time.sleep(counter)
    if buf == "":
        ERROR(url)
    return buf
