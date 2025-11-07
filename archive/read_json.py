import json
import os

# Load configuration from config.json
def get_config():
    config_path = 'config.json'

    if not os.path.exists(config_path):
        print(f"配置文件不存在，请运行‘init_初始化’文件")
        return None, None, None, None

    with open('config.json', 'r', encoding='utf-8') as config_file:
        config = json.load(config_file)
        username = config['username']
        password = config['password']
        net_type = config['net_type']
        should_notify = config['should_notify']
    return username, password, net_type, should_notify


