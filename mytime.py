import os
import datetime
import time
def get_file_modified_time(filename:str):
    filemt = time.localtime(os.stat(filename).st_mtime)
    return time.strftime("%Y-%m-%d", filemt)

def get_mtime(filename):
    t = os.path.getmtime(filename)
    t = datetime.datetime.fromtimestamp(t)
    t = str(t)
    return t

def get_time_now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def get_currentime():
    ctime = get_time_now()
    return f'[{ctime}]    '