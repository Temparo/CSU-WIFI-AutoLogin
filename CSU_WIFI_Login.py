import sys
import json
import os
import time
import requests
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QComboBox, QCheckBox, QMessageBox, QTimeEdit,
                             QGroupBox, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout, QStatusBar)
from PyQt6.QtGui import QIcon, QFont, QDesktopServices
from PyQt6.QtCore import QSettings, QTime, QUrl

class CSUWIFILogin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_path = 'config.json'
        self.current_device_ip = None
        self.current_device_mac = None
        self.init_ui()
        self.load_config()

    def init_ui(self):
        self.setWindowTitle('CSU WIFI AutoLogin')
        self.setWindowIcon(QIcon('assets/wifi_icon_256x256.ico'))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # --- Login Settings Group ---
        login_settings_group = QGroupBox('登录设置')
        login_settings_layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.net_combo = QComboBox()
        self.net_combo.addItems(['中国电信', '中国移动', '中国联通', '校园网'])
        form_layout.addRow('学号:', self.user_input)
        form_layout.addRow('密码:', self.pass_input)
        form_layout.addRow('运营商:', self.net_combo)
        login_settings_layout.addLayout(form_layout)

        options_layout = QHBoxLayout()
        self.auto_login_check = QCheckBox('自动登录')
        self.startup_check = QCheckBox('开机自启')
        self.startup_check.stateChanged.connect(self.handle_startup)
        options_layout.addWidget(self.auto_login_check)
        options_layout.addWidget(self.startup_check)
        options_layout.addStretch()
        login_settings_layout.addLayout(options_layout)

        login_settings_group.setLayout(login_settings_layout)
        layout.addWidget(login_settings_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton('保存配置')
        self.save_btn.clicked.connect(self.save_config)
        self.login_btn = QPushButton('登录')
        self.login_btn.clicked.connect(self.login)
        self.logout_btn = QPushButton('注销')
        self.logout_btn.clicked.connect(self.logout)
        self.status_btn = QPushButton('查询状态')
        self.status_btn.clicked.connect(self.check_status)
        self.refresh_devices_btn = QPushButton('刷新设备')
        self.refresh_devices_btn.clicked.connect(self.refresh_online_devices)
        self.about_btn = QPushButton('关于')
        self.about_btn.clicked.connect(self.open_about_page)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.logout_btn)
        btn_layout.addWidget(self.status_btn)
        btn_layout.addWidget(self.refresh_devices_btn)
        btn_layout.addWidget(self.about_btn)
        layout.addLayout(btn_layout)


        # Scheduled Login Group
        schedule_group = QGroupBox('定时登录')
        schedule_group.setCheckable(True)
        schedule_group.setChecked(False)
        schedule_group_layout = QVBoxLayout()

        # Top row: Time edit and apply button
        top_schedule_layout = QHBoxLayout()
        top_schedule_layout.addWidget(QLabel("执行时间:"))
        self.schedule_time_edit = QTimeEdit()
        self.schedule_time_edit.setDisplayFormat("HH:mm")
        top_schedule_layout.addWidget(self.schedule_time_edit)
        self.schedule_apply_btn = QPushButton('应用定时任务')
        self.schedule_apply_btn.clicked.connect(self.handle_scheduled_task)
        top_schedule_layout.addWidget(self.schedule_apply_btn)
        schedule_group_layout.addLayout(top_schedule_layout)

        # Second row: Schedule type selection
        schedule_type_layout = QHBoxLayout()
        schedule_type_layout.addWidget(QLabel("重复方式:"))
        self.schedule_type_combo = QComboBox()
        self.schedule_type_combo.addItems(["每天", "每隔几天", "每周"])
        self.schedule_type_combo.currentIndexChanged.connect(self.update_schedule_options_ui)
        schedule_type_layout.addWidget(self.schedule_type_combo)
        schedule_group_layout.addLayout(schedule_type_layout)

        # Third row (dynamic): Options for "Every N days" or "Weekly"
        self.schedule_options_widget = QWidget()
        self.schedule_options_layout = QHBoxLayout(self.schedule_options_widget)
        self.schedule_options_layout.setContentsMargins(0, 0, 0, 0)

        # "Every N days" option
        self.days_interval_widget = QWidget()
        days_layout = QHBoxLayout(self.days_interval_widget)
        days_layout.setContentsMargins(0, 0, 0, 0)
        days_layout.addWidget(QLabel("每隔"))
        self.schedule_days_spinbox = QSpinBox()
        self.schedule_days_spinbox.setMinimum(2)
        self.schedule_days_spinbox.setMaximum(365)
        days_layout.addWidget(self.schedule_days_spinbox)
        days_layout.addWidget(QLabel("天"))
        self.schedule_options_layout.addWidget(self.days_interval_widget)

        # "Weekly" option
        self.weekdays_widget = QWidget()
        weekdays_layout = QHBoxLayout(self.weekdays_widget)
        weekdays_layout.setContentsMargins(0, 0, 0, 0)
        self.weekday_checkboxes = {}
        for day_name, day_code in [("一", "MON"), ("二", "TUE"), ("三", "WED"), ("四", "THU"), ("五", "FRI"), ("六", "SAT"), ("日", "SUN")]:
            cb = QCheckBox(day_name)
            self.weekday_checkboxes[day_code] = cb
            weekdays_layout.addWidget(cb)
        self.schedule_options_layout.addWidget(self.weekdays_widget)

        schedule_group_layout.addWidget(self.schedule_options_widget)
        schedule_group.setLayout(schedule_group_layout)
        layout.addWidget(schedule_group)
        self.schedule_group = schedule_group

        # Online Devices Table
        self.online_devices_table = QTableWidget()
        self.online_devices_table.setColumnCount(4)
        self.online_devices_table.setHorizontalHeaderLabels(['IP地址', 'MAC地址', '登录时间', '设备类型'])
        self.online_devices_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.online_devices_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.online_devices_table.setFixedHeight(120)  # Set a fixed height for header + 3 rows
        layout.addWidget(self.online_devices_table)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel('状态: 未登录')
        self.status_bar.addWidget(self.status_label)

        # Set layout margins and spacing
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.user_input.setText(config.get('username', ''))
                self.pass_input.setText(config.get('password', ''))
                self.net_combo.setCurrentText(config.get('net_type', '校园网'))
                self.auto_login_check.setChecked(config.get('auto_login', False))

                # Load schedule config
                self.schedule_group.setChecked(config.get('schedule_enabled', False))
                schedule_time_str = config.get('schedule_time', '08:00')
                self.schedule_time_edit.setTime(QTime.fromString(schedule_time_str, "HH:mm"))
                self.schedule_type_combo.setCurrentText(config.get('schedule_type', '每天'))
                self.schedule_days_spinbox.setValue(config.get('schedule_days_interval', 2))
                selected_weekdays = config.get('schedule_weekdays', [])
                for day_code, checkbox in self.weekday_checkboxes.items():
                    checkbox.setChecked(day_code in selected_weekdays)

                self.update_schedule_options_ui()  # Ensure correct UI state on load

                # Check current online status first
                online = self.check_status()
                # If auto login is enabled and already online, unbind, logout, then login again
                if self.auto_login_check.isChecked():
                    if online:
                        self.unbind()
                        time.sleep(2)
                        self.logout()
                        time.sleep(2)
                        self.login()
                    else:
                        self.login()
                # If not auto-login, just get devices if online
                elif online:
                    self.get_online_devices()
        else:
            # Config does not exist; still check current status
            self.check_status()

    def save_config(self):
        selected_weekdays = [day_code for day_code, cb in self.weekday_checkboxes.items() if cb.isChecked()]
        config = {
            'username': self.user_input.text(),
            'password': self.pass_input.text(),
            'net_type': self.net_combo.currentText(),
            'auto_login': self.auto_login_check.isChecked(),
            'schedule_enabled': self.schedule_group.isChecked(),
            'schedule_time': self.schedule_time_edit.time().toString("HH:mm"),
            'schedule_type': self.schedule_type_combo.currentText(),
            'schedule_days_interval': self.schedule_days_spinbox.value(),
            'schedule_weekdays': selected_weekdays
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
                self.get_online_devices()
            else:
                self.status_label.setText(f'状态: 登录失败 - {response.text}')
        except requests.exceptions.ConnectionError:
            self.status_label.setText('状态: 未连接到校园网，请检查网络连接')
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
                 self.online_devices_table.setRowCount(0)  # Clear table on logout
            else:
                 self.status_label.setText('状态: 注销失败')
        except requests.exceptions.ConnectionError:
            self.status_label.setText('状态: 未连接到校园网，请检查网络连接')
        except requests.RequestException as e:
            self.status_label.setText(f'状态: 注销出错 - {e}')

    def unbind(self):
        username = self.user_input.text()
        if not username:
            self.status_label.setText('状态: 请填写学号以解绑')
            return

        self.status_label.setText('状态: 正在解绑设备...')
        QApplication.processEvents()
        try:
            url = f'https://portal.csu.edu.cn:802/eportal/portal/mac/unbind?user_account={username}'
            response = requests.get(url, timeout=5)
            # Assuming the response text gives a clear indication.
            # You might need to adjust the check based on actual server response.
            if 'success' in response.text or '成功' in response.text:
                self.status_label.setText('状态: 解绑成功')
            else:
                self.status_label.setText(f'状态: 解绑失败 - {response.text}')
        except requests.exceptions.ConnectionError:
            self.status_label.setText('状态: 未连接到校园网，请检查网络连接')
        except requests.RequestException as e:
            self.status_label.setText(f'状态: 解绑出错 - {e}')


    def open_about_page(self):
        url = QUrl("https://github.com/Temparo/CSU-WIFI-AutoLogin/")
        QDesktopServices.openUrl(url)

    def refresh_online_devices(self):
        self.status_label.setText("状态:正在刷新设备列表...")
        QApplication.processEvents()
        self.get_online_devices()

    def get_online_devices(self):
        username = self.user_input.text()
        password = self.pass_input.text()
        if not username or not password:
            self.status_label.setText('状态: 请填写学号和密码以查询设备')
            return

        try:
            # Note: This endpoint requires 'username', not the full 'user_account' with suffix.
            url = f'https://portal.csu.edu.cn:802/eportal/portal/Custom/online_data?username={username}&password={password}'
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            # Process JSONP response
            jsonp_text = response.text
            if jsonp_text.startswith('jsonpReturn(') and jsonp_text.endswith(');'):
                json_str = jsonp_text[len('jsonpReturn('):-2]
                data = json.loads(json_str)

                if data.get("result") == 1:
                    devices = data.get("data", [])
                    self.online_devices_table.setRowCount(len(devices))
                    for i, device in enumerate(devices):
                        device_type = "PC" if device.get("phone_flag") == "0" else "手机"
                        online_ip = device.get('online_ip', '')
                        online_mac = device.get('online_mac', '')

                        # 检查是否为本机
                        if online_ip and online_mac and online_ip == self.current_device_ip and online_mac == self.current_device_mac:
                            device_type += " (本机)"

                        self.online_devices_table.setItem(i, 0, QTableWidgetItem(online_ip))
                        self.online_devices_table.setItem(i, 1, QTableWidgetItem(online_mac))
                        self.online_devices_table.setItem(i, 2, QTableWidgetItem(device.get('online_time', '')))
                        self.online_devices_table.setItem(i, 3, QTableWidgetItem(device_type))
                    self.status_label.setText(f'状态: 已获取在线设备列表，共 {len(devices)} 台设备。')
                else:
                    self.status_label.setText(f'状态: 获取设备列表失败 - {data.get("msg")}')
            else:
                self.status_label.setText('状态: 获取设备列表失败 - 响应格式不正确')

        except requests.exceptions.ConnectionError:
            self.status_label.setText('状态: 未连接到校园网，请检查网络连接')
        except requests.RequestException as e:
            self.status_label.setText(f'状态: 获取设备列表出错 - {e}')
        except json.JSONDecodeError:
            self.status_label.setText('状态: 获取设备列表失败 - 解析响应失败')

    def update_schedule_options_ui(self):
        schedule_type = self.schedule_type_combo.currentText()
        if schedule_type == "每天":
            self.days_interval_widget.hide()
            self.weekdays_widget.hide()
        elif schedule_type == "每隔几天":
            self.days_interval_widget.show()
            self.weekdays_widget.hide()
        elif schedule_type == "每周":
            self.days_interval_widget.hide()
            self.weekdays_widget.show()

    def handle_scheduled_task(self):
        task_name = "CSUWIFILogin_Scheduled"

        if not self.schedule_group.isChecked():
            # Delete task command
            command = f'schtasks /delete /tn "{task_name}" /f'
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    QMessageBox.information(self, '成功', '定时任务已删除。')
                else:
                    # It's okay if the task didn't exist.
                    QMessageBox.information(self, '提示', '定时任务已禁用或不存在。')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'删除定时任务时出错: {e}')
            self.save_config()
            return

        # --- Create or Update Task ---
        app_path = os.path.abspath(sys.argv[0])
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
        else:
            app_path = f'"{sys.executable.replace("python.exe", "pythonw.exe")}" "{os.path.abspath(__file__)}"'

        schedule_time = self.schedule_time_edit.time().toString("HH:mm")
        schedule_type = self.schedule_type_combo.currentText()

        base_command = f'schtasks /create /tn "{task_name}" /tr "{app_path} --auto-login" /st {schedule_time} /f'

        if schedule_type == "每天":
            modifier = "/sc DAILY"
        elif schedule_type == "每隔几天":
            days = self.schedule_days_spinbox.value()
            modifier = f"/sc DAILY /mo {days}"
        elif schedule_type == "每周":
            selected_days = [day_code for day_code, cb in self.weekday_checkboxes.items() if cb.isChecked()]
            if not selected_days:
                QMessageBox.warning(self, '警告', '请至少选择一个星期中的日期。')
                return
            days_str = ",".join(selected_days)
            modifier = f"/sc WEEKLY /d {days_str}"
        else:
            QMessageBox.critical(self, '错误', '未知的计划类型。')
            return

        command = f'{base_command} {modifier}'

        try:
            subprocess.run(command, check=True, shell=True, capture_output=True, text=True)
            QMessageBox.information(self, '成功', '定时任务已成功应用。')
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, '错误', f'应用定时任务失败: {e.stderr}')

        self.save_config()


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

    def check_status(self) -> bool:
        """检查当前网络认证状态
        期望响应格式: ( {"result":1, ...} ) —— 最外层一对括号包裹 JSON 对象。
        返回: bool 表示是否已经在线。
        """
        try:
            dr = ''  # callback 参数，示例为空字符串
            url = f'https://portal.csu.edu.cn/drcom/chkstatus?callback={dr}'
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            raw_text = response.text.strip()

            # 按示例格式解析: ( {...} )
            if not (raw_text.startswith('(') and raw_text.endswith(')')):
                self.status_label.setText('状态: 状态查询失败 - 响应不符合示例格式 (…JSON…)')
                self.current_device_ip = None
                self.current_device_mac = None
                return False

            json_str = raw_text[1:-1]
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                self.status_label.setText('状态: 状态查询失败 - JSON 解析错误')
                self.current_device_ip = None
                self.current_device_mac = None
                return False

            # 判断 result 字段
            if data.get('result') == 1:
                uid = data.get('uid', '')
                v4ip = data.get('v4ip') or data.get('v46ip') or ''
                self.current_device_ip = v4ip
                self.current_device_mac = data.get('olmac')
                self.status_label.setText(f'状态: 已在线 (账号: {uid} IP: {v4ip})')
                return True
            else:
                self.status_label.setText('状态: 当前未在线')
                self.current_device_ip = None
                self.current_device_mac = None
                return False
        except requests.exceptions.ConnectionError:
            self.status_label.setText('状态: 未连接到校园网，请检查网络连接')
            self.current_device_ip = None
            self.current_device_mac = None
            return False
        except requests.RequestException as e:
            self.status_label.setText(f'状态: 状态查询失败 - {e}')
            self.current_device_ip = None
            self.current_device_mac = None
            return False


if __name__ == '__main__':
    # Handle command line arguments for silent auto-login
    if '--auto-login' in sys.argv:
        app = QApplication.instance() # Check if an instance already exists
        if not app:
            app = QApplication(sys.argv)

        # We need to create a dummy window to access config and login methods
        # but we don't show it.
        login_task = CSUWIFILogin()
        login_task.load_config()  # Load config to get credentials
        login_task.login()  # Perform login
        # No app.exec() is called, so the script will exit after login attempt.
        sys.exit(0)


    app = QApplication(sys.argv)

    # 设置全局字体为微软雅黑
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    ex = CSUWIFILogin()
    ex.show()
    sys.exit(app.exec())
