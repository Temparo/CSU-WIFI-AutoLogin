import os
import time

from portal import login, unbind, logout
from read_json import get_config

username, password, net_type, should_notify = get_config()

# 先解绑后自动登录
unbind(username=username)
time.sleep(3)
logout()
time.sleep(3)
login(username=username, password=password, net_type=net_type)
os.system("pause")
