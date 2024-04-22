#!/usr/bin/env python3
# coding: utf-8

import time

from functools import reduce

LOG_TIME_MAP = {}

def LOG_TIME(key, *msg):
    if not key in LOG_TIME_MAP:
        LOG_TIME_MAP[key] = time.time()
    try:
        print(", ".join([str(obj) for obj in [*msg, key]]))
    except Exception as e:
        print(e)

def LOG_TIME_END(key, *msg):
    if key in LOG_TIME_MAP:
        start_time = LOG_TIME_MAP[key]
        gap_time = int((time.time() - start_time) * 1000)
        try:
            print(", ".join([str(obj) for obj in [*msg, key, f"#sec: {gap_time}"]]))
        except Exception as e:
            print(e)
        LOG_TIME_MAP.pop(key)
    else:
        ERROR(f"No LOG_TIME before LOG_TIME_END, key: {key}")

def LOG(*msg):
    try:
        print(", ".join([str(obj) for obj in msg]))
    except Exception as e:
        print(e)


def ERROR(*msg):
    try:
        print(", ".join([str(obj) for obj in msg]))
        _msg = reduce(lambda x, y: "%s %s" % (str(x), str(y)), msg)
        with open("error.txt", "a") as fd:
            fd.write("%s %s\r\n" % (time.time(), _msg))
    except Exception as e:
        print(e)
