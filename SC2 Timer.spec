# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.building.datastruct import TOC


APP_NAME = 'SC2 Timer'
USE_UPX = os.environ.get('SC2_TIMER_USE_UPX', '1') == '1'
SEPARATE_LIBS = os.environ.get('SC2_TIMER_SEPARATE_LIBS', '0') == '1'
OPTIMIZE_OPTIONS = [('O', None, 'OPTION'), ('O', None, 'OPTION')]

EXCLUDED_MODULES = [
    'matplotlib',
    'notebook',
    'pandas',
    'PyQt5.QtNetwork',
    'PyQt5.QtWebEngine',
    'PyQt5.QtWebEngineCore',
    'PyQt5.QtWebEngineWidgets',
    'PyQt5.QtSql',
    'PyQt5.QtXml',
    'cryptography',
    'OpenSSL',
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'pynput',
    'cv2',
    'skimage',
    'torch',
    'numpy',
    'win32ui',
    'Pythonwin',
    'PIL._avif',
    'keyboard._darwinkeyboard',
    'keyboard._nixcommon',
    'keyboard._nixkeyboard',
]

KEEP_QT_IMAGE_FORMATS = {'qgif.dll', 'qico.dll', 'qjpeg.dll', 'qsvg.dll'}
KEEP_QT_PLATFORMS = {'qwindows.dll'}
KEEP_QT_TRANSLATIONS = {
    'qt_zh_CN.qm',
    'qtbase_zh_CN.qm',
    'qt_help_zh_CN.qm',
}


def should_drop_qt_entry(entry):
    name = entry[0].replace('\\', '/')
    basename = os.path.basename(name).lower()

    if name.startswith('PyQt5/Qt5/plugins/platforms/'):
        return basename not in KEEP_QT_PLATFORMS

    if name.startswith('PyQt5/Qt5/plugins/platformthemes/'):
        return True

    if name.startswith('PyQt5/Qt5/plugins/imageformats/'):
        return basename not in KEEP_QT_IMAGE_FORMATS

    if name.startswith('PyQt5/Qt5/translations/'):
        return os.path.basename(name) not in KEEP_QT_TRANSLATIONS

    return False


def filter_qt_entries(entries):
    return TOC(entry for entry in entries if not should_drop_qt_entry(entry))


a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDED_MODULES,
    noarchive=False,
    optimize=2,
)
a.binaries = filter_qt_entries(a.binaries)
a.datas = filter_qt_entries(a.datas)
pyz = PYZ(a.pure)

if SEPARATE_LIBS:
    exe = EXE(
        pyz,
        a.scripts,
        OPTIMIZE_OPTIONS,
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=USE_UPX,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=['ico\\fav.ico'],
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=USE_UPX,
        upx_exclude=[],
        name=APP_NAME,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        OPTIMIZE_OPTIONS,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=USE_UPX,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=['ico\\fav.ico'],
    )
