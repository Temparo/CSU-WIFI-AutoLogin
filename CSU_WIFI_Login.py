import sys
import json
import os
import requests
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QLineEdit, QPushButton, QComboBox, QCheckBox, QMessageBox)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSettings

class CSUWIFILogin(QWidget):
    def __init__(self):
        super().__init__()
        self.config_path = 'config.json'
        self.init_ui()
        self.load_config()

    def init_ui(self):
        self.setWindowTitle('CSU WIFI AutoLogin')
        self.setWindowIcon(QIcon('assets/wifi_icon_256x256.ico'))

        layout = QVBoxLayout()

        # Username
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel('学号:'))
        self.user_input = QLineEdit()
        user_layout.addWidget(self.user_input)
        layout.addLayout(user_layout)

        # Password
        pass_layout = QHBoxLayout()
        pass_layout.addWidget(QLabel('密码:'))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        pass_layout.addWidget(self.pass_input)
        layout.addLayout(pass_layout)

        # Network Type
        net_layout = QHBoxLayout()
        net_layout.addWidget(QLabel('运营商:'))
        self.net_combo = QComboBox()
        self.net_combo.addItems(['中国电信', '中国移动', '中国联通', '校园网'])
        net_layout.addWidget(self.net_combo)
        layout.addLayout(net_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton('保存配置')
        self.save_btn.clicked.connect(self.save_config)
        self.login_btn = QPushButton('登录')
        self.login_btn.clicked.connect(self.login)
        self.logout_btn = QPushButton('注销')
        self.logout_btn.clicked.connect(self.logout)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.logout_btn)
        layout.addLayout(btn_layout)

        # Options
        self.auto_login_check = QCheckBox('自动登录')
        self.startup_check = QCheckBox('开机自启')
        self.startup_check.stateChanged.connect(self.handle_startup)
        layout.addWidget(self.auto_login_check)
        layout.addWidget(self.startup_check)

        # Status
        self.status_label = QLabel('状态: 未登录')
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.user_input.setText(config.get('username', ''))
                self.pass_input.setText(config.get('password', ''))
                self.net_combo.setCurrentText(config.get('net_type', '校园网'))
                self.auto_login_check.setChecked(config.get('auto_login', False))
                if self.auto_login_check.isChecked():
                    self.login()

    def save_config(self):
        config = {
            'username': self.user_input.text(),
            'password': self.pass_input.text(),
            'net_type': self.net_combo.currentText(),
            'auto_login': self.auto_login_check.isChecked()
        }
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
        QMessageBox.information(self, '成功', '配置已保存！')

    def login(self):
        username = self.user_input.text()
        password = self.pass_input.text()
        net_type = self.net_combo.currentText()

        if not username or not password:
            self.status_label.setText('状态: 请填写学号和密码')
            return

        net_types = {
            '中国电信': 'telecomn',
            '中国移动': 'cmccn',
            '中国联通': 'unicomn',
            '校园网': ''
        }
        user_account = f"{username}@{net_types[net_type]}" if net_types[net_type] else username

        self.status_label.setText(f"状态: 正在使用 {net_type} 账户登录...")
        QApplication.processEvents()

        try:
            url = f'https://portal.csu.edu.cn:802/eportal/portal/login?user_account={user_account}&user_password={password}'
            response = requests.get(url, timeout=5)
            if '{"result":1,"msg":"Portal协议认证成功！"}' in response.text:
                self.status_label.setText('状态: 登录成功！')
            else:
                self.status_label.setText(f'状态: 登录失败 - {response.text}')
        except requests.RequestException as e:
            self.status_label.setText(f'状态: 登录出错 - {e}')

    def logout(self):
        self.status_label.setText('状态: 正在注销...')
        QApplication.processEvents()
        try:
            url = 'https://portal.csu.edu.cn:802/eportal/portal/logout'
            response = requests.get(url, timeout=5)
            if 'success' in response.text:
                 self.status_label.setText('状态: 注销成功')
            else:
                 self.status_label.setText('状态: 注销失败')
        except requests.RequestException as e:
            self.status_label.setText(f'状态: 注销出错 - {e}')

    def handle_startup(self, state):
        app_name = "CSUWIFILogin"
        app_path = os.path.abspath(sys.argv[0])

        # For pyinstaller one-file executable
        if getattr(sys, 'frozen', False):
            app_path = sys.executable

        settings = QSettings("HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run", QSettings.Format.NativeFormat)

        if state:
            settings.setValue(app_name, f'"{app_path}"')
        else:
            settings.remove(app_name)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CSUWIFILogin()
    ex.show()
    sys.exit(app.exec())

