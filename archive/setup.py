# setup.py
import json


def validate_input(prompt, valid_options=None):
    while True:
        user_input = input(prompt)
        if valid_options:
            if user_input in valid_options:
                return user_input
            else:
                print(f"输入无效，请输入以下选项之一: {', '.join(valid_options)}")
        else:
            if user_input.strip():
                return user_input
            else:
                print("输入不能为空，请重新输入。")


# Prompt the user for input with validation
username = validate_input("请输入学号: ")
password = validate_input("请输入密码: ")
net_type = validate_input("请选择运营商（中国移动、中国联通、中国电信、校园网）: ",
                          ["中国移动", "中国联通", "中国电信", "校园网"])
should_notify = validate_input("是否发送通知 (是/否): ", ["是", "否"])

# Store the information in a config file
config = {
    "username": username,
    "password": password,
    "net_type": net_type,
    "should_notify": should_notify == '是'
}

with open('auto_login/config.json', 'w', encoding='utf-8') as config_file:
    json.dump(config, config_file, ensure_ascii=False, indent=4)

print("配置信息已保存到 config.json 文件中")
