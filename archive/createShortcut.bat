@echo off
chcp 65001 & cls
echo 正在创建桌面快捷方式，请勿关闭本窗口.

::设置程序或文件的完整路径（必选）
set "Program=%APPDATA%\CSUAutoLogin\auto_login.exe"

::设置快捷方式名称（必选）
set "LnkName=csu-student登录"

::设置程序的工作路径，一般为程序主目录，此项若留空，脚本将自行分析路径
set "WorkDir=%APPDATA%\CSUAutoLogin\"

::设置快捷方式显示的说明（可选）
set "Desc=csu-student校园网自动登录"

:: 检查 Program 路径是否存在
if not exist "%Program%" (
    echo 错误: 程序文件 %Program% 不存在.
    pause
    exit /b 1
)

:: 使用 PowerShell 创建快捷方式
powershell -command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([System.IO.Path]::Combine($WshShell.SpecialFolders('Desktop'), '%LnkName%.lnk')); $Shortcut.TargetPath = '%Program%'; $Shortcut.WorkingDirectory = '%WorkDir%'; $Shortcut.WindowStyle = 1; $Shortcut.Description = '%Desc%'; $Shortcut.Save()"

if %errorlevel% neq 0 (
    echo 错误: PowerShell 执行失败.
    pause
    exit /b 1
)

echo 桌面快捷方式创建成功！
exit