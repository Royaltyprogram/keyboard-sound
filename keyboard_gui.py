import json
import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pygame.mixer
from pynput.keyboard import Key, Listener

# pygame 초기화 (소리 재생을 위해)
pygame.mixer.init()

class KeyboardSoundGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("키보드 사운드 커스터마이저")
        self.root.geometry("1000x600")
        
        # 키 매핑 데이터 로드
        self.key_mapping_file = "keyboard_mapping_t.json"
        self.key_to_mp3 = self.load_key_mapping()
        
        # 키보드 레이아웃 정의
        self.create_keyboard_layout()
        
        # 도구 프레임 생성
        self.create_tool_frame()
        
        # 키보드 리스너 설정
        self.listener = None
        self.start_listener()
        
        # 소리 캐시
        self.sound_cache = {}
        
        # 현재 눌린 키를 추적
        self.pressed_keys = set()
        
        # 종료 시 리소스 정리
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_key_mapping(self):
        """JSON 파일에서 키보드 매핑 데이터를 로드합니다."""
        try:
            if os.path.exists(self.key_mapping_file):
                with open(self.key_mapping_file, 'r', encoding='utf-8') as f:
                    mapping = json.load(f)
                    print(f"키 매핑 로드 성공: {len(mapping)}개 매핑")
                    return mapping
            else:
                print(f"매핑 파일을 찾을 수 없음: {self.key_mapping_file}")
                return {}
        except Exception as e:
            print(f"키 매핑 로드 실패: {e}")
            return {}
    
    def save_key_mapping(self):
        """현재 키 매핑 데이터를 JSON 파일로 저장합니다."""
        try:
            with open(self.key_mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.key_to_mp3, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("저장 완료", f"{self.key_mapping_file}에 매핑이 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("저장 실패", f"매핑 저장 중 오류 발생: {e}")
    
    def create_tool_frame(self):
        """도구 프레임을 생성합니다."""
        self.tool_frame = ttk.Frame(self.root, padding=10)
        self.tool_frame.pack(side=tk.TOP, fill=tk.X)
        
        # 저장 버튼
        ttk.Button(self.tool_frame, text="매핑 저장", command=self.save_key_mapping).pack(side=tk.LEFT, padx=5)
        
        # 새 매핑 로드 버튼
        ttk.Button(self.tool_frame, text="매핑 로드", command=self.load_new_mapping).pack(side=tk.LEFT, padx=5)
        
        # 도움말 버튼
        ttk.Button(self.tool_frame, text="도움말", command=self.show_help).pack(side=tk.LEFT, padx=5)
        
        # 현재 선택된 키 정보 표시
        self.selected_key_label = ttk.Label(self.tool_frame, text="선택된 키: 없음")
        self.selected_key_label.pack(side=tk.LEFT, padx=20)
        
        # 할당된 소리 표시
        self.sound_path_label = ttk.Label(self.tool_frame, text="할당된 소리: 없음")
        self.sound_path_label.pack(side=tk.LEFT, padx=5)
    
    def create_keyboard_layout(self):
        """키보드 레이아웃을 생성합니다."""
        self.keyboard_frame = ttk.Frame(self.root, padding=10)
        self.keyboard_frame.pack(fill=tk.BOTH, expand=True)
        
        # 키보드 레이아웃 정의
        keyboard_layout = [
            [('`', 1), ('1', 1), ('2', 1), ('3', 1), ('4', 1), ('5', 1), ('6', 1), ('7', 1), ('8', 1), ('9', 1), ('0', 1), ('-', 1), ('=', 1), ('backspace', 2)],
            [('tab', 1.5), ('q', 1), ('w', 1), ('e', 1), ('r', 1), ('t', 1), ('y', 1), ('u', 1), ('i', 1), ('o', 1), ('p', 1), ('[', 1), (']', 1), ('\\', 1.5)],
            [('caps_lock', 1.8), ('a', 1), ('s', 1), ('d', 1), ('f', 1), ('g', 1), ('h', 1), ('j', 1), ('k', 1), ('l', 1), (';', 1), ('\'', 1), ('enter', 2.2)],
            [('shift', 2.5), ('z', 1), ('x', 1), ('c', 1), ('v', 1), ('b', 1), ('n', 1), ('m', 1), (',', 1), ('.', 1), ('/', 1), ('shift_r', 2.5)],
            [('ctrl', 1.5), ('cmd', 1.5), ('alt', 1.5), ('space', 6), ('alt_r', 1.5), ('cmd_r', 1.5), ('ctrl_r', 1.5)]
        ]
        
        # 키 버튼 저장 딕셔너리
        self.key_buttons = {}
        
        # 각 행의 키보드 레이아웃 생성
        for row_idx, row in enumerate(keyboard_layout):
            row_frame = ttk.Frame(self.keyboard_frame)
            row_frame.pack(pady=5, fill=tk.X)
            
            for key_info in row:
                key_name, width_ratio = key_info
                self.create_key_button(row_frame, key_name, width_ratio)
        
        # 화살표 키 추가
        arrow_frame = ttk.Frame(self.keyboard_frame)
        arrow_frame.pack(pady=5)
        
        # 위쪽 화살표
        self.create_key_button(arrow_frame, 'up', 1)
        
        # 왼쪽, 아래쪽, 오른쪽 화살표를 담을 프레임
        bottom_arrows = ttk.Frame(arrow_frame)
        bottom_arrows.pack()
        
        self.create_key_button(bottom_arrows, 'left', 1)
        self.create_key_button(bottom_arrows, 'down', 1)
        self.create_key_button(bottom_arrows, 'right', 1)
        
        # 기능 키 추가 (F1-F12)
        function_frame = ttk.Frame(self.keyboard_frame)
        function_frame.pack(pady=5, fill=tk.X)
        
        for i in range(1, 13):
            self.create_key_button(function_frame, f'f{i}', 1)
    
    def create_key_button(self, parent, key_name, width_ratio):
        """키 버튼을 생성합니다."""
        key_width = int(60 * width_ratio)
        
        # 버튼 스타일 설정
        style = ttk.Style()
        style.configure("Key.TButton", padding=5)
        
        # 키 버튼 생성
        key_button = ttk.Button(
            parent, 
            text=key_name.upper() if len(key_name) > 1 else key_name,
            width=width_ratio,
            style="Key.TButton",
            command=lambda k=key_name: self.on_key_button_click(k)
        )
        key_button.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 버튼 저장
        self.key_buttons[key_name] = key_button
    
    def on_key_button_click(self, key_name):
        """키 버튼 클릭 이벤트 핸들러."""
        self.selected_key_label.config(text=f"선택된 키: {key_name}")
        
        # 현재 할당된 소리 표시
        sound_path = self.key_to_mp3.get(key_name, "할당되지 않음")
        self.sound_path_label.config(text=f"할당된 소리: {os.path.basename(sound_path)}")
        
        # 새 소리 할당
        new_sound = filedialog.askopenfilename(
            title=f"{key_name} 키에 할당할 소리 선택",
            filetypes=[("MP3 파일", "*.mp3"), ("모든 파일", "*.*")]
        )
        
        if new_sound:
            # 상대 경로로 저장
            if os.path.isabs(new_sound):
                rel_path = os.path.relpath(new_sound, os.getcwd())
                self.key_to_mp3[key_name] = rel_path
            else:
                self.key_to_mp3[key_name] = new_sound
            
            # 캐시에서 제거하여 새 소리가 로드되도록
            if key_name in self.sound_cache:
                del self.sound_cache[key_name]
            
            # 라벨 업데이트
            self.sound_path_label.config(text=f"할당된 소리: {os.path.basename(new_sound)}")
    
    def start_listener(self):
        """키보드 리스너를 시작합니다."""
        self.listener = Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.listener.start()
    
    def on_key_press(self, key):
        """키가 눌렸을 때의 이벤트 핸들러."""
        try:
            # 키 이름 가져오기
            if hasattr(key, 'char') and key.char is not None:
                k = key.char
            else:
                k = str(key).replace('Key.', '')
            
            # 이미 눌려있는 키는 무시
            if k in self.pressed_keys:
                return
            
            self.pressed_keys.add(k)
            
            # GUI 업데이트는 메인 스레드에서 처리
            self.root.after(0, lambda: self.highlight_key(k, True))
            
            # 소리 재생
            self.play_sound(k)
                
        except Exception as e:
            print(f"키 눌림 이벤트 처리 오류: {e}")
    
    def on_key_release(self, key):
        """키가 떼어졌을 때의 이벤트 핸들러."""
        try:
            # 키 이름 가져오기
            if hasattr(key, 'char') and key.char is not None:
                k = key.char
            else:
                k = str(key).replace('Key.', '')
            
            # 누른 키 목록에서 제거
            if k in self.pressed_keys:
                self.pressed_keys.remove(k)
            
            # GUI 업데이트는 메인 스레드에서 처리
            self.root.after(0, lambda: self.highlight_key(k, False))
                
        except Exception as e:
            print(f"키 뗌 이벤트 처리 오류: {e}")
    
    def highlight_key(self, key_name, is_pressed):
        """키 버튼의 상태를 시각적으로 업데이트합니다."""
        if key_name in self.key_buttons:
            button = self.key_buttons[key_name]
            if is_pressed:
                # 키가 눌렸을 때 스타일 변경
                button.state(['pressed'])
                button.configure(style="Pressed.Key.TButton")
            else:
                # 키가 떼어졌을 때 스타일 복원
                button.state(['!pressed'])
                button.configure(style="Key.TButton")
    
    def play_sound(self, key_name):
        """키에 맵핑된 소리를 재생합니다."""
        if key_name in self.key_to_mp3:
            sound_path = self.key_to_mp3[key_name]
            
            # 소리 캐싱
            if key_name not in self.sound_cache:
                try:
                    sound = pygame.mixer.Sound(sound_path)
                    self.sound_cache[key_name] = sound
                except Exception as e:
                    print(f"소리 로드 실패 ({key_name}): {e}")
                    return
            
            # 소리 재생
            try:
                self.sound_cache[key_name].play()
            except Exception as e:
                print(f"소리 재생 실패 ({key_name}): {e}")
    
    def load_new_mapping(self):
        """새 매핑 파일을 로드합니다."""
        file_path = filedialog.askopenfilename(
            title="매핑 파일 선택",
            filetypes=[("JSON 파일", "*.json"), ("모든 파일", "*.*")]
        )
        
        if file_path:
            self.key_mapping_file = file_path
            self.key_to_mp3 = self.load_key_mapping()
            messagebox.showinfo("로드 완료", f"{file_path}에서 매핑이 로드되었습니다.")
            
            # 소리 캐시 초기화
            self.sound_cache.clear()
    
    def show_help(self):
        """도움말을 표시합니다."""
        help_text = """
        키보드 사운드 커스터마이저 사용법:
        
        1. 키보드 레이아웃에서 키를 클릭하여 해당 키에 소리를 할당할 수 있습니다.
        2. 눌린 키는 시각적으로 강조됩니다.
        3. '매핑 저장' 버튼을 클릭하여 현재 키 매핑을 저장할 수 있습니다.
        4. '매핑 로드' 버튼을 클릭하여 기존 매핑 파일을 로드할 수 있습니다.
        
        실시간으로 키를 누르면 할당된 소리가 재생됩니다.
        """
        messagebox.showinfo("도움말", help_text)
    
    def on_closing(self):
        """애플리케이션 종료 시 정리 작업을 수행합니다."""
        if self.listener:
            self.listener.stop()
        self.root.destroy()

if __name__ == "__main__":
    # 스타일 설정
    root = tk.Tk()
    style = ttk.Style()
    
    # 키 버튼 스타일 정의
    style.configure("Key.TButton", padding=5, relief="raised")
    style.configure("Pressed.Key.TButton", padding=5, relief="sunken", background="#aaccff")
    
    app = KeyboardSoundGUI(root)
    root.mainloop() 