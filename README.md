# 中南校园网助手（CSU-WIFI-AutoLogin）

Windows 一键登录 CSU-Student（CSU-WIFI），支持自动登录、定时登录、开机自启、设备管理。

<img src="assets/Screenshot.png" alt="Screenshot" width="70%"></div>

---

## 快速开始

1. 下载 [最新版本](https://github.com/Temparo/CSU-WIFI-AutoLogin/releases/latest)
2. 双击运行 `CSU-WIFI-AutoLogin.exe`

## 功能

- ✅ 开机自启：电脑开机时启动应用，自动连接校园网
- ✅ 定时登录：使用Windows定时任务，指定时间自动连接（电脑开机且登录状态下）
- ✅ 设备管理：查看校园网在线设备
- ✅ 理论上可以用于CSU-Student/CSU-WIFI/CSU-教职工，但目前只对CSU-Student进行了测试

## 开发

```bash
# 安装依赖
pip install PyQt6 requests keyring

# 启动应用
python CSU_WIFI_Login.py

```

## 反馈

如遇问题，请[创建 Issue](https://github.com/Temparo/CSU-WIFI-AutoLogin/issues)，并附：

- 复现步骤
- 相关截图

## 声明与致谢

- 接口参考：[CSU-Net-Portal](https://github.com/barkure/CSU-Net-Portal)
- 仅用于简化合法校园网登录，请遵守学校网络规范
- 接口或策略变动可能导致功能失效

