# CSU-WIFI-AutoLogin
在Windows系统下，自动（一键）登录中南大学校园网，保持校园网登录态。
可以选择，或者设置定时任务。

根据[CSU-Net-Portal](https://github.com/barkure/CSU-Net-Portal)修改而来，非常感谢原作者。

## 使用方法

1. 下载Release中的[ win_v0.2.7z ](https://github.com/CSU-Index/CSU-WIFI-AutoLogin/releases/download/v0.2/win_v0.2.7z)
   ，解压到任意目录
2. 运行`install.bat`，程序会自动弹出配置窗口，输入信息后安装

可以使用“Windows 任务计划”（如每周日运行一次）或设置开机自启动

## 卸载方法

运行`uninstall.bat`卸载程序，或手动删除`%APPDATA%\CSUAutoLogin`文件夹和桌面快捷方式。

## 配置存储与安全

- 非敏感配置（如用户名、网络类型、定时设置）不再使用单独的 `config.json` 文件，统一使用 QSettings 存储。
    - Windows 下默认写入注册表：`HKEY_CURRENT_USER/Software/CSU/WifiAutoLogin`
- 密码不写入任何文件，使用系统凭据库存储：在 Windows 上通过 keyring 使用 Credential Manager。

## 打包与依赖

- 依赖：`PyQt6`、`requests`、`keyring`
- 如使用 PyInstaller 打包，若遇到 keyring 后端导入问题，可添加隐藏导入：
    - `--hidden-import keyring.backends.Windows`
- 计划任务与自动登录需要在与保存密码相同的 Windows 用户上下文下运行，才能读取凭据。
