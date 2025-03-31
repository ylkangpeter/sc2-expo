import ctypes
from ctypes import wintypes

# 加载 DLL
user32 = ctypes.windll.user32
shcore = ctypes.windll.shcore  # 获取 DPI 的库

# 结构体定义
class MONITORINFOEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),  # 物理显示器区域
        ("rcWork", wintypes.RECT),  # 工作区域（不包含任务栏）
        ("dwFlags", wintypes.DWORD),  # 是否是主显示器
        ("szDevice", wintypes.WCHAR * 32)  # 设备名称
    ]

# 回调函数定义
MonitorEnumProc = ctypes.WINFUNCTYPE(
    wintypes.BOOL,  # 返回值类型
    wintypes.HMONITOR,  # 显示器句柄 (HMONITOR)
    wintypes.HDC,  # 设备上下文句柄 (HDC)
    ctypes.POINTER(wintypes.RECT),  # 显示器矩形区域 (LPRECT)
    wintypes.LPARAM  # 自定义参数 (LPARAM)
)

monitors = []

# 获取 DPI
def get_dpi_for_monitor(hMonitor):
    dpi_x = wintypes.UINT()
    dpi_y = wintypes.UINT()
    
    # 仅 Windows 8.1+ 支持 GetDpiForMonitor
    result = shcore.GetDpiForMonitor(hMonitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
    if result == 0:  # S_OK
        return dpi_x.value, dpi_y.value
    return 96, 96  # 默认 96 DPI（100% 缩放）

# 遍历显示器
def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
    info = MONITORINFOEX()
    info.cbSize = ctypes.sizeof(MONITORINFOEX)

    # 确保 hMonitor 类型正确
    hMonitor = ctypes.cast(hMonitor, wintypes.HMONITOR)

    if user32.GetMonitorInfoW(hMonitor, ctypes.byref(info)):
        dpi_x, dpi_y = get_dpi_for_monitor(hMonitor)  # 获取 DPI

        monitors.append({
            "Device Name": info.szDevice,
            "Monitor Area": (info.rcMonitor.left, info.rcMonitor.top, info.rcMonitor.right, info.rcMonitor.bottom),
            "Work Area": (info.rcWork.left, info.rcWork.top, info.rcWork.right, info.rcWork.bottom),
            "Primary": bool(info.dwFlags & 1),
            "DPI_X": dpi_x,
            "DPI_Y": dpi_y
        })
    return True

# 设置 DPI 感知，使得 DPI API 可用
try:
    user32.SetProcessDpiAwareness(2)  # 让进程感知 DPI 变化
except AttributeError:
    pass  # 低版本 Windows 没有这个 API

# 遍历所有显示器
user32.EnumDisplayMonitors(None, None, MonitorEnumProc(monitor_enum_proc), 0)

# 打印所有监视器信息
for monitor in monitors:
    print(monitor)
