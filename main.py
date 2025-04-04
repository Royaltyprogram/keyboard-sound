import logging
import pyaudio
import json
import os
import threading
import time
import numpy as np
from pydub import AudioSegment
from pynput.keyboard import Key, Listener

pa = None

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

# 전역 PyAudio 초기화
pa = pyaudio.PyAudio()
active_audio_segments = []
active_audio_lock = threading.Lock()

def mixer_thread():
    # Determine output audio parameters using defaults or the first loaded audio
    sample_width = 2
    channels = 2
    rate = 44100
    if key_to_audio:
        first_audio = next(iter(key_to_audio.values()))
        sample_width = first_audio.sample_width
        channels = first_audio.channels
        rate = first_audio.frame_rate
    
    stream = pa.open(
        format=pa.get_format_from_width(sample_width),
        channels=channels,
        rate=rate,
        output=True,
        frames_per_buffer=256
    )
    
    chunk_size = 256  # frames per buffer
    while True:
        with active_audio_lock:
            if not active_audio_segments:
                # Write silence if no active audio segments
                silence = (np.zeros(chunk_size * channels, dtype=np.int16)).tobytes()
                stream.write(silence)
            else:
                mixed_chunk = None
                segments_to_remove = []
                for segment in active_audio_segments:
                    audio_seg = segment['audio']
                    offset = segment['offset']
                    bytes_per_frame = audio_seg.sample_width * audio_seg.channels
                    chunk_byte_length = chunk_size * bytes_per_frame
                    data_chunk = audio_seg.raw_data[offset:offset+chunk_byte_length]
                    if len(data_chunk) < chunk_byte_length:
                        data_chunk += b'\x00' * (chunk_byte_length - len(data_chunk))
                        segments_to_remove.append(segment)
                    # Convert the chunk to a numpy array (assuming 16-bit samples)
                    chunk_array = np.frombuffer(data_chunk, dtype=np.int16)
                    if mixed_chunk is None:
                        mixed_chunk = chunk_array.astype(np.int32)
                    else:
                        mixed_chunk += chunk_array.astype(np.int32)
                    # Update offset for this segment
                    segment['offset'] += chunk_byte_length
                # Remove finished segments
                for seg in segments_to_remove:
                    active_audio_segments.remove(seg)
                if mixed_chunk is not None:
                    # Clip to int16 range and write to stream
                    mixed_chunk = np.clip(mixed_chunk, -32768, 32767).astype(np.int16)
                    stream.write(mixed_chunk.tobytes())
        # Small sleep to yield CPU if needed
        time.sleep(0.001)

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
        logging.info(f"Queueing preloaded audio for key: {k}")
        with active_audio_lock:
            active_audio_segments.append({ 'audio': key_to_audio[k], 'offset': 0 })
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

# Start the mixer thread
mixer = threading.Thread(target=mixer_thread, daemon=True)
mixer.start()

# 키보드 이벤트 리스너 시작
with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

# 프로그램 종료 후 자원 정리
pa.terminate()