@echo off
REM 设置命令行使用 UTF-8 编码
chcp 65001

REM 打印日志：开始脚本执行
echo -------------------------------
echo 开始脚本执行...
echo -------------------------------

REM 获取当前登录用户
set USERNAME=%USERNAME%
echo 当前登录用户: %USERNAME%

REM 设置目标路径（加上引号处理空格）
set TARGET_DIR=C:\Users\%USERNAME%\Documents\StarCraft II\Accounts
echo 目标路径: "%TARGET_DIR%"

REM 获取最新修改的文件夹
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
REM 使用时间戳作为文件名
set FILENAME=快捷施法_%TIME::=%
REM 移除文件名中的小数点
set FILENAME=%FILENAME:.=%
echo 生成的文件名: %FILENAME%.txt

REM 打印日志：开始复制文件（加上引号处理空格）
echo 正在复制文件...
copy "快捷施法设置.txt" "C:\Users\%USERNAME%\Documents\StarCraft II\Accounts\%LATEST_FOLDER%\Hotkeys\%FILENAME%.SC2Hotkeys"
if %errorlevel% == 0 (
    echo 文件 "%FILENAME%.txt" 已成功创建并复制内容。
) else (
    echo 发生错误：文件复制失败。
    goto :error
)

REM 打印日志：脚本执行完毕
echo -------------------------------
echo 脚本执行完毕。
echo -------------------------------
pause
goto :eof

:error
echo -------------------------------
echo 脚本执行失败。
echo -------------------------------
pause
