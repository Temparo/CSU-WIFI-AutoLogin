import sys
import json
import os
import requests
import subprocess
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QComboBox, QCheckBox, QMessageBox, QTimeEdit,
                             QGroupBox, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QStatusBar,
                             QGridLayout)
from PyQt6.QtGui import QIcon, QFont, QDesktopServices
from PyQt6.QtCore import QSettings, QTime, QUrl, QTimer
import secure_storage

# QSettings organization/application identifiers
ORG_NAME = "CSU"
APP_NAME = "WifiAutoLogin"

# Added: resource_path helper to support PyInstaller one-file (_MEIPASS)
def resource_path(relative: str) -> str:
    """Return absolute path to resource, compatible with PyInstaller bundled executable."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(getattr(sys, '_MEIPASS'), relative)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, relative)

class CSUWIFILogin(QMainWindow):
    def __init__(self, headless: bool = False):
        """Create main window.
        headless=True 用于计划任务或命令行静默执行，不启动自动登录的定时 QTimer 序列。"""
        super().__init__()
        self.headless = headless  # 记录是否为无界面/静默模式
        self.settings = QSettings(ORG_NAME, APP_NAME)
        self.current_device_ip = None
        self.current_device_mac = None
        self.init_ui()
        # 在初始化后加载配置；根据 headless 状态决定是否启动自动登录序列
        self.load_config(suppress_auto_sequence=headless)

    def init_ui(self):
        self.setWindowTitle('CSU WIFI AutoLogin')
        # Changed: use resource_path for icon
        self.setWindowIcon(QIcon(resource_path('assets/wifi_icon_256x256.ico')))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # --- Login Settings Group ---
        login_settings_group = QGroupBox('登录设置')
        login_settings_layout = QGridLayout() # Use QGridLayout for better alignment

        # Form fields
        self.user_input = QLineEdit()
        self.user_input.setToolTip('请输入您的学号')
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setToolTip('请输入您的密码')
        self.net_combo = QComboBox()
        self.net_combo.addItems(['中国电信', '中国移动', '中国联通', '校园网'])
        self.net_combo.setToolTip('请选择您使用的运营商')

        login_settings_layout.addWidget(QLabel('学号:'), 0, 0)
        login_settings_layout.addWidget(self.user_input, 0, 1)
        login_settings_layout.addWidget(QLabel('密码:'), 1, 0)
        login_settings_layout.addWidget(self.pass_input, 1, 1)
        login_settings_layout.addWidget(QLabel('运营商:'), 2, 0)
        login_settings_layout.addWidget(self.net_combo, 2, 1)

        # Checkboxes
        self.auto_login_check = QCheckBox('自动登录')
        self.auto_login_check.setToolTip('程序启动时自动使用保存的配置进行登录')
        self.startup_check = QCheckBox('开机自启')
        self.startup_check.setToolTip('设置程序是否在系统启动时自动运行')
        self.startup_check.stateChanged.connect(self.handle_startup)
        self.auto_exit_check = QCheckBox('自动退出')
        self.auto_exit_check.setToolTip('登录成功后自动关闭程序')

        # Create horizontal layout for checkboxes to keep them left-aligned
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.auto_login_check)
        checkbox_layout.addWidget(self.startup_check)
        checkbox_layout.addWidget(self.auto_exit_check)
        checkbox_layout.addStretch()  # Push checkboxes to the left

        login_settings_layout.addLayout(checkbox_layout, 3, 0, 1, 2)  # Span 2 columns

        login_settings_group.setLayout(login_settings_layout)
        layout.addWidget(login_settings_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton('保存配置')
        self.save_btn.clicked.connect(self.save_config)
        self.login_btn = QPushButton('登录')
        self.login_btn.clicked.connect(self.gui_login)
        self.logout_btn = QPushButton('注销')
        self.logout_btn.clicked.connect(self.logout)
        self.status_btn = QPushButton('查询状态')
        self.status_btn.clicked.connect(self.check_status)
        self.refresh_devices_btn = QPushButton('刷新设备')
        self.refresh_devices_btn.clicked.connect(self.refresh_online_devices)
        self.about_btn = QPushButton('关于')
        self.about_btn.clicked.connect(self.open_about_page)

        # Core actions
        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.logout_btn)
        btn_layout.addStretch()

        # Auxiliary actions
        btn_layout.addWidget(self.status_btn)
        btn_layout.addWidget(self.refresh_devices_btn)
        btn_layout.addStretch()

        # Secondary actions
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.about_btn)
        layout.addLayout(btn_layout)


        # Scheduled Login Group
        schedule_group = QGroupBox('定时登录')
        schedule_group.setCheckable(True)
        schedule_group.setChecked(False)
        schedule_group_layout = QVBoxLayout()

        # Help text
        schedule_help_label = QLabel('启用后，将在指定时间自动执行登录操作。')
        schedule_help_label.setStyleSheet("color: gray;")
        schedule_group_layout.addWidget(schedule_help_label)

        # Top row: Time edit and apply button
        top_schedule_layout = QHBoxLayout()
        top_schedule_layout.addWidget(QLabel("执行时间:"))
        self.schedule_time_edit = QTimeEdit()
        self.schedule_time_edit.setDisplayFormat("HH:mm")
        self.schedule_time_edit.setToolTip('设置任务执行的具体时间')
        top_schedule_layout.addWidget(self.schedule_time_edit)
        self.schedule_apply_btn = QPushButton('应用定时任务')
        self.schedule_apply_btn.setToolTip('创建或更新Windows计划任务')
        self.schedule_apply_btn.clicked.connect(self.handle_scheduled_task)
        top_schedule_layout.addWidget(self.schedule_apply_btn)
        schedule_group_layout.addLayout(top_schedule_layout)

        # Second row: Schedule type selection
        schedule_type_layout = QHBoxLayout()
        schedule_type_layout.addWidget(QLabel("重复方式:"))
        self.schedule_type_combo = QComboBox()
        self.schedule_type_combo.addItems(["每天", "每隔几天", "每周"])
        self.schedule_type_combo.setToolTip('选择任务的重复频率')
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

    def load_config(self, suppress_auto_sequence: bool = False):
        """Load UI state from QSettings (no file-based config).
        Password is fetched from keyring (if available) based on username.
        suppress_auto_sequence=True 时不执行自动登录定时逻辑（用于静默任务）。"""
        username = self.settings.value('login/username', '', str)
        net_type = self.settings.value('login/net_type', '校园网', str)
        auto_login = self.settings.value('login/auto_login', False, bool)
        auto_exit = self.settings.value('login/auto_exit', False, bool)
        schedule_enabled = self.settings.value('schedule/enabled', False, bool)
        schedule_time = self.settings.value('schedule/time', '08:00', str)
        schedule_type = self.settings.value('schedule/type', '每天', str)
        schedule_days_interval = int(self.settings.value('schedule/days_interval', 2))
        schedule_weekdays_raw = self.settings.value('schedule/weekdays', '', str)
        selected_weekdays = [d for d in schedule_weekdays_raw.split(',') if d] if schedule_weekdays_raw else []

        # Populate UI
        self.user_input.setText(username)
        if username:
            self.pass_input.setText(secure_storage.get_password(username) or '')
        else:
            self.pass_input.setText('')
        self.net_combo.setCurrentText(net_type)
        self.auto_login_check.setChecked(auto_login)
        self.auto_exit_check.setChecked(auto_exit)

        self.schedule_group.setChecked(schedule_enabled)
        self.schedule_time_edit.setTime(QTime.fromString(schedule_time, "HH:mm"))
        self.schedule_type_combo.setCurrentText(schedule_type)
        self.schedule_days_spinbox.setValue(schedule_days_interval)
        for day_code, checkbox in self.weekday_checkboxes.items():
            checkbox.setChecked(day_code in selected_weekdays)
        self.update_schedule_options_ui()

        # Online status & optional auto-login (仅非 headless 并且未被抑制时执行定时序列)
        if (not suppress_auto_sequence) and (not self.headless) and self.auto_login_check.isChecked():
            self._start_auto_login_sequence()
        else:
            online = self.check_status()
            if online and (not self.headless):
                self.get_online_devices()

    def _start_auto_login_sequence(self):
        """Begin non-blocking auto-login sequence using timers instead of sleep.
        内部自己检查在线状态，避免外层重复判断。"""
        already_online = self.check_status()
        if already_online:
            self.unbind()
            # Use an instance-based single-shot timer to avoid type checker warnings and ensure lifetime
            self._auto_timer1 = QTimer(self)
            self._auto_timer1.setSingleShot(True)
            self._auto_timer1.timeout.connect(self._auto_login_do_logout)
            self._auto_timer1.start(2000)
        else:
            self.login()

    def _auto_login_do_logout(self):
        self.logout()
        # Chain next step with another single-shot timer
        self._auto_timer2 = QTimer(self)
        self._auto_timer2.setSingleShot(True)
        self._auto_timer2.timeout.connect(self.login)
        self._auto_timer2.start(2000)

    def run_headless_auto_login_sequence(self, delay_seconds: int = 2) -> None:
        """在静默模式下以阻塞方式执行 解绑→延时→注销→延时→登录。
        无需事件循环与 QTimer，适用于 --auto-login 与计划任务。

        delay_seconds: 两步动作之间的等待秒数，默认 2 秒，与 GUI 定时器一致。
        """
        # 即使未在线，执行注销也不会造成问题；按指定顺序强制执行可最大化成功率。
        self.unbind()
        time.sleep(max(0, delay_seconds))
        self.logout()
        time.sleep(max(0, delay_seconds))
        self.login()

    def save_config(self):
        """Persist current UI state to QSettings (except password)."""
        selected_weekdays = [day_code for day_code, cb in self.weekday_checkboxes.items() if cb.isChecked()]
        self.settings.setValue('login/username', self.user_input.text().strip())
        self.settings.setValue('login/net_type', self.net_combo.currentText())
        self.settings.setValue('login/auto_login', self.auto_login_check.isChecked())
        self.settings.setValue('login/auto_exit', self.auto_exit_check.isChecked())
        self.settings.setValue('schedule/enabled', self.schedule_group.isChecked())
        self.settings.setValue('schedule/time', self.schedule_time_edit.time().toString("HH:mm"))
        self.settings.setValue('schedule/type', self.schedule_type_combo.currentText())
        self.settings.setValue('schedule/days_interval', self.schedule_days_spinbox.value())
        self.settings.setValue('schedule/weekdays', ','.join(selected_weekdays))

        # Store or clear password in keyring
        username = self.user_input.text().strip()
        pwd = self.pass_input.text()
        if username and pwd:
            secure_storage.set_password(username, pwd)
        elif username and not pwd:
            secure_storage.delete_password(username)
        QMessageBox.information(self, '成功', '配置已保存！')

    def gui_login(self):
        """GUI登录按钮点击处理方法。
        验证输入后，直接调用自动登录序列。
        自动登录序列内部会检查在线状态：
        已在线：解绑→延时→注销→延时→登录
        未在线：直接登录"""
        username = self.user_input.text()
        password = self.pass_input.text()
        # If password empty, try to fetch from keyring lazily
        if not password and username:
            kp = secure_storage.get_password(username)
            if kp:
                password = kp
                self.pass_input.setText(kp)

        if not username or not password:
            self.status_label.setText('状态: 请填写学号和密码')
            return

        # 直接调用自动登录序列，内部会判断在线状态
        self._start_auto_login_sequence()

    def login(self):
        username = self.user_input.text()
        password = self.pass_input.text()
        # If password empty, try to fetch from keyring lazily
        if not password and username:
            kp = secure_storage.get_password(username)
            if kp:
                password = kp
                self.pass_input.setText(kp)
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
                # Check if auto-exit is enabled
                if self.auto_exit_check.isChecked():
                    QApplication.processEvents()
                    sys.exit(0)
            else:
                self.status_label.setText(f'状态: 登录失败 - {response.text}')
        except requests.exceptions.Timeout:
            self.status_label.setText('状态: 请求超时，请稍后重试')
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
                 self.online_devices_table.setRowCount(0)
            else:
                 self.status_label.setText('状态: 注销失败')
        except requests.exceptions.Timeout:
            self.status_label.setText('状态: 请求超时，请稍后重试')
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
        except requests.exceptions.Timeout:
            self.status_label.setText('状态: 请求超时，请稍后重试')
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
        # If password empty, try to fetch from keyring lazily
        if not password and username:
            kp = secure_storage.get_password(username)
            if kp:
                password = kp
                self.pass_input.setText(kp)
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

        except requests.exceptions.Timeout:
            self.status_label.setText('状态: 请求超时，请稍后重试')
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
        # 使用统一构造函数生成静默运行命令
        invoke_cmd = self._build_headless_invoke_cmd()

        schedule_time = self.schedule_time_edit.time().toString("HH:mm")
        schedule_type = self.schedule_type_combo.currentText()

        base_command = f'schtasks /create /tn "{task_name}" /tr "{invoke_cmd}" /st {schedule_time} /f'

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

    def _build_headless_invoke_cmd(self) -> str:
        """构造一次性静默运行命令，返回完整命令字符串，路径已加引号。"""
        if getattr(sys, 'frozen', False):
            return f'"{sys.executable}" --auto-login'
        python_exec = sys.executable
        py_dir = os.path.dirname(python_exec)
        pythonw_candidate = os.path.join(py_dir, 'pythonw.exe')
        if os.path.basename(python_exec).lower() == 'python.exe' and os.path.exists(pythonw_candidate):
            interpreter = f'"{pythonw_candidate}"'
        else:
            interpreter = f'"{python_exec}"'
        script_path = f'"{os.path.abspath(__file__)}"'
        return f'{interpreter} {script_path} --auto-login'

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
        返回: bool 表示是否已经在线。"""
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
        except requests.exceptions.Timeout:
            self.status_label.setText('状态: 请求超时，请稍后重试')
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

        # headless 模式：以同步方式执行 解绑→延时→注销→延时→登录
        login_task = CSUWIFILogin(headless=True)
        login_task.run_headless_auto_login_sequence(delay_seconds=2)
        # No app.exec() is called, so the script will exit after the attempt.
        sys.exit(0)


    app = QApplication(sys.argv)

    # 设置全局字体为微软雅黑
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    ex = CSUWIFILogin()
    ex.show()
    sys.exit(app.exec())
