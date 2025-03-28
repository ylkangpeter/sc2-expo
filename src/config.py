# current region
current_region = 'kr'  # 当前地区 / Current region
current_language = 'zh'  # 当前语言 / Current language


# 调试模式配置
debug_mode = True  # 设置为True启用调试模式 / Set to True to enable debug mode
debug_time_factor = 5.0  # 调试模式下的时间流速因子 / Time flow factor in debug mode

# 日志级别配置
LOG_LEVEL = 'INFO'  # 日志级别，可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL / Log level, available values: DEBUG, INFO, WARNING, ERROR, CRITICAL

# 快捷键
MAP_SHORTCUT = 'ctrl + shift + ['  # 地图快捷键 / Map shortcut key
LOCK_SHORTCUT = 'ctrl + shift + ]'  # 锁定快捷键 / Lock shortcut key

# Toast提示配置
TOAST_ALLOWED = True  # 是否允许显示Toast提示 / Whether to allow displaying Toast notifications
TOAST_DURATION = 10000  # 显示时间（毫秒）/ Display time (in milliseconds)
TOAST_OPACITY = 0  # 背景透明度（0-255）/ Background opacity (0-255)
TOAST_POSITION = 0.9  # 垂直位置（窗口高度的比例）/ Vertical position (relative to window height)
TOAST_FONT_SIZE = 45  # 字体大小 / Font size
TOAST_FONT_COLOR = 'rgb(0, 191, 255)'  # 字体颜色 / Font color

# 窗体设置项
# 主窗口透明度配置 ，最后一个200为透明度，前面三个数是RGB数值，具体可以网上查一下选一个自己喜欢的颜色，0完全透明、255完全不透明 / 0 fully transparent, 255 fully opaque
MAIN_WINDOW_BG_COLOR = 'rgba(43, 43, 43, 200)' # 主界面背景设置
COMMANDER_SELECTOR_BG_COLOR = 'rgba(43, 43, 43, 200)'  # 指挥官选择器背景设置
# 窗体宽度 注意这里没有对按钮之类的宽度进行适配，改了之后主要影响的是表格中文字显示的宽度
MAIN_WINDOW_WIDTH = 167  # 主窗口宽度 / Main window width

# 表格字体大小
TABLE_FONT_SIZE = 12  # 表格字体大小 / Table font size
TABLE_HEIGHT = 185 # 表格高度
TABLE_FONT_COLOR = 'rgb(255, 255, 255)'  # 表格字体颜色 / Table font color


# 时间提醒配置
TIME_ALERT_SECONDS = 60  # 提前提醒时间（秒）/ Time before alert (in seconds)

# 突变因子提醒配置
MUTATION_FACTOR_ALERT_SECONDS = 30  # 突变因子提前提醒时间（秒）/ Mutation factor alert time (in seconds)
MUTATION_FACTOR_ALERT_DURATION_SECONDS = 5  # 突变因子提醒持续时间（秒）/ Duration of mutation factor alert (in seconds)
MUTATION_ALERT_TOAST_POSITION = 0.7  # 垂直位置（窗口高度的比例）/ Vertical position (relative to window height)
MUTATOR_DEPLOYMENT_COLOR = 'rgb(0, 255, 128)'  # 突变因子部署颜色 / Mutator deployment color
MUTATOR_RIFTS_COLOR = 'rgb(0, 255, 128)'  # 突变因子裂隙颜色 / Mutator rifts color
MUTATOR_PROPAGATOR_COLOR = 'rgb(0, 255, 128)'  # 突变因子传播者颜色 / Mutator propagator color

# 突变因子提示位置配置
MUTATOR_TOAST_POSITION = 0.7  # 垂直位置（窗口高度的比例）/ Vertical position (relative to window height)
MUTATOR_ICON_TRANSPARENCY = 0.7  # 突变因子图标透明度 / Mutator icon transparency
TOAST_MUTATOR_FONT_SIZE = 30  # 突变因子提示字体大小 / Mutator toast font size
MUTATOR_DEPLOYMENT_POS = 0.2  # 突变因子部署位置 / Mutator deployment position
MUTATOR_PROPAGATOR_POS = 0.35  # 突变因子传播者位置 / Mutator propagator position
MUTATOR_RIFT_POS = 0.5  # 突变因子裂隙位置 / Mutator rift position
MUTATOR_KILLBOTS_POS = 0.65  # 突变因子杀戮机器人位置 / Mutator killbots position
MUTATOR_BOMBBOTS_POS = 0.8  # 突变因子炸弹机器人位置 / Mutator bombbots position

# wiki url
WIKI_URL = 'https://starcraft.huijiwiki.com/wiki/%E5%90%88%E4%BD%9C%E4%BB%BB%E5%8A%A1/%E7%AA%81%E5%8F%98%E5%88%97%E8%A1%A8'  # Wiki链接 / Wiki URL

# 指挥官头像布局
avatar = [
    ['raynor', 'kerrigan', 'artanis', 'swann', 'zagara', 'vorazun', 'karax', 'abathur', 'alarak', 'nova'],  # 第一行指挥官头像 / First row of commander avatars
    ['stukov', 'fenix', 'dehaka', 'horner', 'tychus', 'zeratul', 'stetmann', 'mengsk']  # 第二行指挥官头像 / Second row of commander avatars
]

# 替换指挥官黑名单 - Mutator commander blacklist
# 添加格式 如：BLACK_LIST = ['raynor', 'kerrigan']， 这样在替换界面点击随机时，就不会替换到这两个了
# If you add commanders like: BLACK_LIST = ['raynor', 'kerrigan'], they won't be selected in random replacement
BLACK_LIST = []


#############################
# 下面配置主要用于图像识别
DEBUG_SHOW_ENEMY_INFO_SQUARE = True  # 是否显示敌方单位信息框 / Whether to show enemy unit information boxes
GAME_SCREEN = 0
GAME_ICON_POS_AMON_RACE = [50, 200, 50, 50] # [x_from_right, y_from_bottom, width, height] 
GAME_ICON_POS_AMON_TROOPS = [200, 250, 200, 80] # [x_from_right, y_from_bottom, width, height
GAME_ICON_POS_MALFUNCTION_PROBE = [10, 200, 300, 30] # [x_from_left, y_from_top, width, height] 

TROOP_ICON_SIZE = 50
TROOP_HYBRID_ICON_COLOR = 'rgb(0, 255, 128)'
TROOP_HYBRCONT_FONT_SIZE = 20