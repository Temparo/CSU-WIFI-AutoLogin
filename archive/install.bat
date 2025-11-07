@echo off
chcp 65001 & cls
title CSUAutoLogin安装程序
:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"
:--------------------------------------
setlocal enabledelayedexpansion

:: 检查配置是否存在，如果不存在则运行配置
if not exist "%source_folder%\config.json" (
    echo 配置不存在，正在运行配置...
    call setup.exe
    if not exist "%source_folder%\config.json" (
        echo 配置失败，退出安装。
        exit /b 1
    )
)

:: 设置源目录和目标目录
set "source_folder=%cd%\auto_login"
set "target_folder=%APPDATA%\CSUAutoLogin"

:: 检查源目录是否存在，如果不存在则退出
if not exist "%source_folder%" (
    echo ERROR: 位置 "%source_folder%" 不存在，请重新输入
    exit /b
)

:: 检查目标目录是否存在，如果不存在则创建
if not exist "%target_folder%" (
    echo WARNING: 位置 "%target_folder%" 不存在，正在创建…
    mkdir "%target_folder%"
)

:: 遍历源目录及其子目录中的所有文件夹
for /d /r "%source_folder%" %%d in (*) do (
    set "subdir=%%d"
    set "relative_path=!subdir:%source_folder%=!"
    set "target_subdir=%target_folder%!relative_path!"

    :: 创建目标子目录
    if not exist "!target_subdir!" (
        mkdir "!target_subdir!"
    )

    :: 移动文件夹内容
    for %%f in ("!subdir!\*") do (
        move "%%f" "!target_subdir!" >nul
    )
)

:: 移动源目录中的所有文件
for /r "%source_folder%" %%f in (*) do (
    set "file=%%f"
    set "relative_path=!file:%source_folder%=!"
    set "target_file=%target_folder%!relative_path!"

    :: 创建目标子目录
    if not exist "!target_file!" (
        move "%%f" "!target_file!" >nul
    )
)

:: 递归删除空文件夹
:delEmptyDirs
for /f "delims=" %%d in ('dir "%source_folder%" /ad /b /s ^| sort /r') do (
    rd "%%d" 2>nul
)
rd "%source_folder%" 2>nul

echo 所有文件和文件夹移动成功

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
pause
