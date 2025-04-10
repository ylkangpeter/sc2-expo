@echo off
chcp 65001

echo -------------------------------
echo 脚本执行开始... >nul
echo -------------------------------

set BACKUP_FILE=注册表备份_%TIME::=%
set BACKUP_FILE=%BACKUP_FILE:.=%.reg

echo 备份原始注册表值到 "%BACKUP_FILE%"... >nul
reg export "HKEY_CURRENT_USER\Control Panel\Accessibility\Keyboard Response" "%BACKUP_FILE%" /y

if %errorlevel% == 0 (
    echo 备份成功，原始注册表值已保存到 "%BACKUP_FILE%"
) else (
    echo 备份失败，请检查权限或路径问题。
    pause
    exit /b
)

echo 正在修改注册表值...

echo ======== 修改 AutoRepeatDelay 为 1000 ========
reg add "HKEY_CURRENT_USER\Control Panel\Accessibility\Keyboard Response" /v AutoRepeatDelay /t REG_SZ /d "100" /f

echo ======== 修改 AutoRepeatRate 为 6 ========
reg add "HKEY_CURRENT_USER\Control Panel\Accessibility\Keyboard Response" /v AutoRepeatRate /t REG_SZ /d "6" /f

echo ======== 修改 DelayBeforeAcceptance 为 0 ========
reg add "HKEY_CURRENT_USER\Control Panel\Accessibility\Keyboard Response" /v DelayBeforeAcceptance /t REG_SZ /d "0" /f

echo 注册表值已成功修改。如需要还原，双击【注册表备份_xxx.reg】文件重新导入即可

echo -------------------------------
echo 脚本执行完毕。
echo -------------------------------

pause