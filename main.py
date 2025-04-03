import logging
import pyaudio
import json
import os
import threading
import time
from pydub import AudioSegment
from pynput.keyboard import Key, Listener

# 로깅 설정: 파일과 콘솔 모두에 로그를 남길 수 있도록 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("./logs/keyboard_events.log", encoding='utf-8')
    ]
)

# JSON 파일에서 키 매핑 로드
def load_key_mapping(json_file="keyboard_mapping_t.json"): #-t (test용)
    """JSON 파일에서 키보드 매핑 데이터를 로드합니다."""
    try:
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                logging.info(f"키 매핑 로드 성공: {len(mapping)}개 매핑")
                return mapping
        else:
            logging.error(f"매핑 파일을 찾을 수 없음: {json_file}")
            return {}
    except Exception as e:
        logging.error(f"키 매핑 로드 실패: {e}")
        return {}

# 키 매핑 로드  (78개)
key_to_mp3 = load_key_mapping()

# Preload audio segments to reduce playback delay
key_to_audio = {}
for k, file_path in key_to_mp3.items():
    try:
        audio_segment = AudioSegment.from_mp3(file_path)
        key_to_audio[k] = audio_segment
        logging.info(f"Preloaded audio for key: {k}")
    except Exception as e:
        logging.error(f"Failed to preload audio for key {k} from file {file_path}: {e}")

def play_audio(audio, start_time=None):
    """
    pyaudio를 통해 preloaded audio segment를 재생합니다.
    """
    if start_time is not None:
        delay = time.time() - start_time
        logging.info(f"Audio playback delay: {delay:.4f} seconds")

    try:
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(audio.sample_width),
                        channels=audio.channels,
                        rate=audio.frame_rate,
                        output=True)

        stream.write(audio.raw_data)

        stream.stop_stream()
        stream.close()
        p.terminate()
    except Exception as e:
        logging.error(f"Audio playback failed: {e}")

def on_press(key):
    """
    키가 눌렸을 때 호출되는 콜백 함수.
    매핑된 키인 경우 해당 mp3 파일을 재생합니다.
    """
    try:
        k = key.char  # 알파벳, 숫자 등 일반 키
    except AttributeError:
        # 특수 키를 문자열로 변환 (Key.space -> 'space')
        k = str(key).replace('Key.', '')

    logging.info(f"Key pressed: {k}")

    if k in key_to_audio:
        logging.info(f"Playing preloaded audio for key: {k}")
        start_time = time.time()
        threading.Thread(target=play_audio, args=(key_to_audio[k], start_time), daemon=True).start()
    else:
        logging.info(f"No audio mapping for key: {k}")

def on_release(key):
    """
    키가 릴리즈될 때 호출되는 콜백 함수.
    Esc 키를 누르면 리스너를 종료합니다.
    """
    logging.info(f"Key released: {key}")
    if key == Key.esc:
        return False  # 리스너 종료

# 키보드 이벤트 리스너 시작
with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()