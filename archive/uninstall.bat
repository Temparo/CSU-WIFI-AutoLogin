@echo off
chcp 65001 & cls
title CSUAutoLogin卸载程序
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

:: 设置目标目录
set "target_folder=%APPDATA%\CSUAutoLogin"

:: 检查目标目录是否存在，如果存在则删除
if exist "%target_folder%" (
    echo 正在删除目标目录 "%target_folder%"...
    rd /s /q "%target_folder%"
    if '%errorlevel%' NEQ '0' (
        echo ERROR: 无法删除目标目录 "%target_folder%"，请手动删除.
        exit /b 1
    )
    echo 目标目录删除成功.
) else (
    echo WARNING: 目标目录 "%target_folder%" 不存在.
)

:: 删除桌面快捷方式
set "LnkName=csu-student登录"
set "shortcut=%USERPROFILE%\Desktop\%LnkName%.lnk"

if exist "%shortcut%" (
    echo 正在删除桌面快捷方式 "%shortcut%"...
    del "%shortcut%"
    if '%errorlevel%' NEQ '0' (
        echo ERROR: 无法删除桌面快捷方式 "%shortcut%"，请手动删除.
        exit /b 1
    )
    echo 桌面快捷方式删除成功.
) else (
    echo WARNING: 桌面快捷方式 "%shortcut%" 不存在.
)

echo 卸载完成！
pause