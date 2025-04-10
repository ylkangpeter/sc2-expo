@echo off
chcp 65001
setlocal enabledelayedexpansion

echo -------------------------------
echo 开始脚本执行...
echo -------------------------------

set USERNAME=%USERNAME%
echo 当前登录用户: %USERNAME%

set TARGET_DIR=C:\Users\%USERNAME%\Documents\StarCraft II\Accounts
echo 目标路径: "%TARGET_DIR%"

echo 正在查找最新修改的文件夹...
if not exist "%TARGET_DIR%" (
    echo 错误：目标路径不存在！
    goto :error
)

for /f "delims=" %%a in ('dir "%TARGET_DIR%" /ad /b /o-d 2^>nul') do (
    set LATEST_FOLDER=%%a
    echo 找到最新文件夹: %%a
    goto :found
)

echo 错误：未找到任何文件夹！
goto :error

:found
set FILENAME=快捷施法_%TIME::=%  
set FILENAME=%FILENAME:.=%  
set FILENAME=%FILENAME: =%  
set FILENAME=!FILENAME: =! 
echo 生成的文件名: %FILENAME%.txt

echo 正在复制文件...
copy "快捷施法设置.txt" "C:\Users\%USERNAME%\Documents\StarCraft II\Accounts\%LATEST_FOLDER%\Hotkeys\%FILENAME%.SC2Hotkeys"
if %errorlevel% == 0 (
    echo 文件 "%FILENAME%.txt" 已成功创建并复制内容。
) else (
    echo 发生错误：文件复制失败。
    goto :error
)

echo -------------------------------
echo 脚本执行完毕。
echo -------------------------------

echo 请选择操作
echo 1-打开开目录查看快捷施法配置
echo 2-退出程序

set /p userChoice="请输入选项(1-2): "

if "%userChoice%"=="2" goto :eof
if "%userChoice%"=="1" (
    "C:\Windows\explorer.exe" "C:\Users\%USERNAME%\Documents\StarCraft II\Accounts\%LATEST_FOLDER%\Hotkeys"
    goto :eof
)

goto :eof

:error
echo -------------------------------
echo 脚本执行失败。
echo -------------------------------
pause
