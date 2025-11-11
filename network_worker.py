"""
异步网络操作工作线程模块。

提供专用的 QThread worker 类，处理所有网络请求，
确保 UI 主线程不会被阻塞。
"""

import json
import requests
from typing import Dict, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal


class NetworkWorker(QThread):
    """后台网络请求工作线程。

    使用 PyQt 信号机制与主线程通信，所有网络操作都在独立线程中执行。
    """

    # 信号定义
    login_finished = pyqtSignal(bool, str)  # (success, message)
    logout_finished = pyqtSignal(bool, str)  # (success, message)
    unbind_finished = pyqtSignal(bool, str)  # (success, message)
    status_finished = pyqtSignal(bool, dict)  # (is_online, data)
    devices_finished = pyqtSignal(bool, list, str)  # (success, devices, message)

    def __init__(self):
        super().__init__()
        self._operation = None
        self._params = {}

    def set_login_task(self, user_account: str, password: str) -> None:
        """设置登录任务参数。"""
        self._operation = 'login'
        self._params = {
            'user_account': user_account,
            'password': password
        }

    def set_logout_task(self) -> None:
        """设置注销任务。"""
        self._operation = 'logout'
        self._params = {}

    def set_unbind_task(self, username: str) -> None:
        """设置解绑任务参数。"""
        self._operation = 'unbind'
        self._params = {'username': username}

    def set_status_check_task(self) -> None:
        """设置状态检查任务。"""
        self._operation = 'check_status'
        self._params = {}

    def set_devices_query_task(self, username: str, password: str) -> None:
        """设置查询在线设备任务参数。"""
        self._operation = 'get_devices'
        self._params = {
            'username': username,
            'password': password
        }

    def run(self) -> None:
        """执行设置的网络任务。由 start() 方法调用。"""
        if self._operation == 'login':
            self._do_login()
        elif self._operation == 'logout':
            self._do_logout()
        elif self._operation == 'unbind':
            self._do_unbind()
        elif self._operation == 'check_status':
            self._do_check_status()
        elif self._operation == 'get_devices':
            self._do_get_devices()

    def _do_login(self) -> None:
        """执行登录操作。"""
        user_account = self._params.get('user_account', '')
        password = self._params.get('password', '')

        try:
            url = f'https://portal.csu.edu.cn:802/eportal/portal/login?user_account={user_account}&user_password={password}'
            response = requests.get(url, timeout=5)

            if '{"result":1,"msg":"Portal协议认证成功！"}' in response.text:
                self.login_finished.emit(True, '登录成功！')
            else:
                self.login_finished.emit(False, f'登录失败 - {response.text}')
        except requests.exceptions.Timeout:
            self.login_finished.emit(False, '请求超时，请关闭代理服务器、加速器、VPN等应用（如有）后重试')
        except requests.exceptions.ConnectionError:
            self.login_finished.emit(False, '未连接到校园网，请检查网络连接')
        except requests.RequestException as e:
            self.login_finished.emit(False, f'登录出错 - {e}')

    def _do_logout(self) -> None:
        """执行注销操作。"""
        try:
            url = 'https://portal.csu.edu.cn:802/eportal/portal/logout'
            response = requests.get(url, timeout=5)

            if 'success' in response.text:
                self.logout_finished.emit(True, '注销成功')
            else:
                self.logout_finished.emit(False, '注销失败')
        except requests.exceptions.Timeout:
            self.logout_finished.emit(False, '请求超时，请关闭代理服务器、加速器、VPN等应用（如有）后重试')
        except requests.exceptions.ConnectionError:
            self.logout_finished.emit(False, '未连接到校园网，请检查网络连接')
        except requests.RequestException as e:
            self.logout_finished.emit(False, f'注销出错 - {e}')

    def _do_unbind(self) -> None:
        """执行解绑设备操作。"""
        username = self._params.get('username', '')

        try:
            url = f'https://portal.csu.edu.cn:802/eportal/portal/mac/unbind?user_account={username}'
            response = requests.get(url, timeout=5)

            if 'success' in response.text or '成功' in response.text:
                self.unbind_finished.emit(True, '解绑成功')
            else:
                self.unbind_finished.emit(False, f'解绑失败 - {response.text}')
        except requests.exceptions.Timeout:
            self.unbind_finished.emit(False, '请求超时，请关闭代理服务器、加速器、VPN等应用（如有）后重试')
        except requests.exceptions.ConnectionError:
            self.unbind_finished.emit(False, '未连接到校园网，请检查网络连接')
        except requests.RequestException as e:
            self.unbind_finished.emit(False, f'解绑出错 - {e}')

    def _do_check_status(self) -> None:
        """执行状态检查操作。"""
        try:
            dr = ''
            url = f'https://portal.csu.edu.cn/drcom/chkstatus?callback={dr}'
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            raw_text = response.text.strip()

            # 解析响应格式: ( {...} )
            if not (raw_text.startswith('(') and raw_text.endswith(')')):
                self.status_finished.emit(False, {'error': '响应格式不正确'})
                return

            json_str = raw_text[1:-1]
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                self.status_finished.emit(False, {'error': 'JSON解析错误'})
                return

            # 判断 result 字段
            if data.get('result') == 1:
                self.status_finished.emit(True, data)
            else:
                self.status_finished.emit(False, data)
        except requests.exceptions.Timeout:
            self.status_finished.emit(False, {'error': '请求超时，请关闭代理服务器、加速器、VPN等应用（如有）后重试'})
        except requests.exceptions.ConnectionError:
            self.status_finished.emit(False, {'error': '未连接到校园网，请检查网络连接'})
        except requests.RequestException as e:
            self.status_finished.emit(False, {'error': f'状态查询失败 - {e}'})

    def _do_get_devices(self) -> None:
        """���行获取在线设备列表操作。"""
        username = self._params.get('username', '')
        password = self._params.get('password', '')

        try:
            url = f'https://portal.csu.edu.cn:802/eportal/portal/Custom/online_data?username={username}&password={password}'
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            # 处理 JSONP 响应
            jsonp_text = response.text
            if jsonp_text.startswith('jsonpReturn(') and jsonp_text.endswith(');'):
                json_str = jsonp_text[len('jsonpReturn('):-2]
                data = json.loads(json_str)

                if data.get("result") == 1:
                    devices = data.get("data", [])
                    self.devices_finished.emit(True, devices, f'已获取在线设备列表，共 {len(devices)} 台设备。')
                else:
                    self.devices_finished.emit(False, [], f'获取设备列表失败 - {data.get("msg")}')
            else:
                self.devices_finished.emit(False, [], '获取设备列表失败 - 响应格式不正确')
        except requests.exceptions.Timeout:
            self.devices_finished.emit(False, [], '请求超时，请关闭代理服务器、加速器、VPN等应用（如有）后重试')
        except requests.exceptions.ConnectionError:
            self.devices_finished.emit(False, [], '未连接到校园网，请检查网络连接')
        except requests.RequestException as e:
            self.devices_finished.emit(False, [], f'获取设备列表出错 - {e}')
        except json.JSONDecodeError:
            self.devices_finished.emit(False, [], '获取设备列表失败 - 解析响应失败')

