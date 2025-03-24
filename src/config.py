# 调试模式配置
debug_mode = False  # 设置为True启用调试模式
debug_time_factor = 5.0  # 调试模式下的时间流速因子

# 日志级别配置
LOG_LEVEL = 'WARNING'  # 日志级别，可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL

# 快捷键
MAP_SHORTCUT = 'ctrl + shift + ['
LOCK_SHORTCUT = 'ctrl + shift + ]'

# Toast提示配置
TOAST_DURATION = 10000  # 显示时间（毫秒）
TOAST_OPACITY = 0    # 背景透明度（0-255）
TOAST_POSITION = 0.9  # 垂直位置（窗口高度的比例）
TOAST_FONT_SIZE = 45
TOAST_FONT_COLOR = 'rgb(0, 191, 255)'

# 时间提醒配置
TIME_ALERT_SECONDS = 60  # 提前提醒时间（秒）

# 突变因子提醒配置
MUTATION_FACTOR_ALERT_SECONDS = 30  # 突变因子提前提醒时间（秒）
MUTATION_FACTOR_ALERT_DURATION_SECONDS = 5  # 突变因子提醒持续事件（秒）
MUTATION_ALERT_TOAST_POSITION = 0.7  # 垂直位置（窗口高度的比例）
MUTATOR_DEPLOYMENT_COLOR = 'rgb(0, 255, 128)'
MUTATOR_RIFTS_COLOR = 'rgb(0, 255, 128)'
MUTATOR_PROPAGATOR_COLOR = 'rgb(0, 255, 128)'

# 突变因子提示位置配置
MUTATOR_TOAST_POSITION = 0.7  # 垂直位置（窗口高度的比例）
MUTATOR_ICON_TRANSPARENCY = 0.7
TOAST_MUTATOR_FONT_SIZE = 30
MUTATOR_DEPLOYMENT_POS=0.2
MUTATOR_PROPAGATOR_POS=0.35
MUTATOR_RIFT_POS=0.5
MUTATOR_KILLBOTS_POS=0.65
MUTATOR_BOMBBOTS_POS=0.8

# wiki url
WIKI_URL = 'https://starcraft.huijiwiki.com/wiki/%E5%90%88%E4%BD%9C%E4%BB%BB%E5%8A%A1/%E7%AA%81%E5%8F%98%E5%88%97%E8%A1%A8'

# 指挥官头像布局
avatar = [
    ['raynor', 'kerrigan', 'artanis', 'swann', 'zagara', 'vorazun', 'karax', 'abathur', 'alarak', 'nova'],
    ['stukov', 'fenix', 'dehaka', 'horner', 'tychus', 'zeratul', 'stetmann', 'mengsk']
]
# 替换指挥官黑名单
BLACK_LIST = [] # 添加格式 如：BLACK_LIST = ['raynor', 'kerrigan']， 这样在替换界面点击随机时，就不会替换到这两个了