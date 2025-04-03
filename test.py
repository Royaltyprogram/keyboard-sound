import logging
from pynput import keyboard

# 로깅 설정: 시간과 메시지를 함께 출력
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def on_press(key):
    """
    키가 눌렸을 때 호출되는 함수.
    문자 키의 경우 key.char, 특수 키의 경우 key를 출력합니다.
    """
    try:
        # 일반 문자 키인 경우
        logging.info(f"Key pressed: {key.char}")
    except AttributeError:
        # 특수 키인 경우 (예: shift, ctrl 등)
        logging.info(f"Special key pressed: {key}")

# 키보드 리스너 시작
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()