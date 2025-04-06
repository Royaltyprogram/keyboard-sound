from setuptools import setup

APP = ['keyboard_gui.py']
DATA_FILES = [
    ('sounds', ['sounds/a.mp3']),  # sounds 디렉토리의 모든 mp3 파일
    ('', ['keyboard_mapping_t.json'])  # 키 매핑 파일
]
OPTIONS = {
    'argv_emulation': True,
    'packages': ['pygame', 'pynput', 'pydub'],
    'iconfile': 'app_icon.icns',  # 아이콘 파일이 있다면 지정
    'plist': {
        'CFBundleName': '키보드 사운드 커스터마이저',
        'CFBundleDisplayName': '키보드 사운드 커스터마이저',
        'CFBundleGetInfoString': '키보드 사운드를 커스터마이징하는 애플리케이션',
        'CFBundleIdentifier': 'com.yourdomain.keyboardsound',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': '© 2024 Your Name',
        'NSHighResolutionCapable': True,
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
) 