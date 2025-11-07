# CSU-WIFI-AutoLogin
在Windows系统下，自动（一键）登录中南大学校园网，保持校园网登录态。
可以选择，或者设置定时任务。

根据[CSU-Net-Portal](https://github.com/barkure/CSU-Net-Portal)修改而来。

## 使用方法

1. 下载Release中的[ win_v0.2.7z ](https://github.com/CSU-Index/CSU-WIFI-AutoLogin/releases/download/v0.2/win_v0.2.7z)
   ，解压到任意目录
2. 运行`install.bat`，程序会自动弹出配置窗口，输入信息后安装

可以使用“Windows 任务计划”（如每周日运行一次）或设置开机自启动

## 卸载方法

运行`uninstall.bat`卸载程序，或手动删除`%APPDATA%\CSUAutoLogin`文件夹和桌面快捷方式。
