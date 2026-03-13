import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import threading
import os
from pathlib import Path
import shutil
import datetime
from sources import icon
import base64

try:
    from moviepy import VideoFileClip

    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        from moviepy.editor import VideoFileClip

        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False

try:
    import cv2

    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# Настройка темы
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class VideoConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Video Konvert")
        self.geometry("580x650")
        self.minsize(580, 650)
        self.set_icon_from_base64()

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.format_var = tk.StringVar(value="MP4")
        self.quality_var = tk.StringVar(value="high")
        self.progress_var = tk.DoubleVar(value=0)

        self.format_extensions = {
            "MP4": "mp4",
            "AVI": "avi",
            "MOV": "mov",
            "MKV": "mkv",
            "WebM": "webm",
            "3GP": "3gp",
            "FLV": "flv"
        }

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        # Заголовок
        ctk.CTkLabel(self, text="Video Konvert", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0,
                                                                                                pady=20)

        # Выбор файла
        input_f = ctk.CTkFrame(self)
        input_f.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        input_f.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(input_f, text="Файл:").grid(row=0, column=0, padx=10)
        ctk.CTkEntry(input_f, textvariable=self.input_path).grid(row=0, column=1, padx=5, pady=15, sticky="ew")
        ctk.CTkButton(input_f, text="Обзор", width=90, command=self.select_input).grid(row=0, column=2, padx=10)

        # Формат и Качество
        settings_f = ctk.CTkFrame(self)
        settings_f.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(settings_f, text="Формат:").grid(row=0, column=0, padx=15, pady=15)
        self.format_menu = ctk.CTkOptionMenu(settings_f, values=list(self.format_extensions.keys()),
                                             variable=self.format_var, command=self.on_format_change)
        self.format_menu.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(settings_f, text="Качество:").grid(row=0, column=2, padx=20)
        self.quality_menu = ctk.CTkSegmentedButton(settings_f, values=["low", "medium", "high", "max"],
                                                   variable=self.quality_var)
        self.quality_menu.grid(row=0, column=3, padx=10)

        # Папка сохранения
        folder_f = ctk.CTkFrame(self)
        folder_f.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.folder_label = ctk.CTkLabel(folder_f, text="Папка: Та же, что у оригинала", text_color="gray")
        self.folder_label.pack(side="left", padx=10, pady=10)
        ctk.CTkButton(folder_f, text="Папка", width=90, command=self.select_folder).pack(side="right", padx=10)

        # Лог
        self.log_text = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.log_text.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")

        # Прогресс и Кнопка
        self.p_bar = ctk.CTkProgressBar(self, variable=self.progress_var)
        self.p_bar.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        self.p_bar.set(0)

        self.start_btn = ctk.CTkButton(self, text="НАЧАТЬ КОНВЕРТАЦИЮ", height=60,
                                       font=ctk.CTkFont(size=18, weight="bold"),
                                       fg_color="#2eb872", hover_color="#1e8551", command=self.start_process)
        self.start_btn.grid(row=6, column=0, padx=20, pady=(10, 20), sticky="ew")

    def log(self, msg):
        self.log_text.insert("end", f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see("end")
        self.update()

    def on_format_change(self, _):
        self.update_output_path()

    def select_input(self):
        f = filedialog.askopenfilename()
        if f:
            self.input_path.set(f)
            self.update_output_path()

    def select_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.custom_folder = d
            self.folder_label.configure(text=f"Папка: {d}", text_color="#3b8ed0")
            self.update_output_path()

    def update_output_path(self):
        if not self.input_path.get():
            return
        p = Path(self.input_path.get())
        d = Path(getattr(self, 'custom_folder', p.parent))
        ext = self.format_extensions.get(self.format_var.get(), "mp4")

        name = f"{p.stem}_converted.{ext}"
        self.output_path.set(str(d / name))
        self.log(f"Цель: {name}")

    def start_process(self):
        if not self.input_path.get():
            return
        self.start_btn.configure(state="disabled")
        threading.Thread(target=self.run_conversion, daemon=True).start()

    def run_conversion(self):
        try:
            self.progress_var.set(0.1)
            inp, outp = self.input_path.get(), self.output_path.get()

            self.log(f"Начало конвертации: {inp} -> {outp}")

            if MOVIEPY_AVAILABLE:
                self.convert_moviepy(inp, outp)
            else:
                self.convert_opencv(inp, outp)

            # Проверяем, создался ли файл
            if os.path.exists(outp):
                file_size = os.path.getsize(outp)
                self.log(f"✅ Файл создан: {outp} (размер: {file_size} байт)")
                self.progress_var.set(1.0)
                self.log("✅ Успех!")
                messagebox.showinfo("Готово", f"Видео сохранено!\n{outp}")
            else:
                self.log("❌ Файл не был создан!")
                messagebox.showerror("Ошибка", "Файл не был создан")

        except Exception as e:
            self.log(f"❌ Ошибка: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.start_btn.configure(state="normal")

    def convert_moviepy(self, inp, outp):
        self.log(f"Обработка через MoviePy...")
        clip = VideoFileClip(inp)

        # Высокие битрейты для качества
        br_map = {"max": "30000k", "high": "16000k", "medium": "8000k", "low": "3000k"}
        br = br_map.get(self.quality_var.get(), "8000k")

        clip.write_videofile(
            outp,
            bitrate=br,
            codec="libx264",
            audio=True,
            audio_codec="aac",
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            preset="slow",
            logger=None
        )
        clip.close()

    def convert_opencv(self, inp, outp):
        self.log("⚠️ MoviePy недоступен. OpenCV пишет БЕЗ ЗВУКА.")
        cap = cv2.VideoCapture(inp)
        fps = cap.get(cv2.CAP_PROP_FPS)
        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out = cv2.VideoWriter(outp, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
        cap.release()
        out.release()

    def set_icon_from_base64(self):
        """Устанавливает иконку из base64 строки"""
        try:
            icon_data = icon.icon_data
            icon_bytes = base64.b64decode(icon_data)

            temp_icon_path = os.path.join(os.environ['TEMP'], 'temp_icon.ico')
            with open(temp_icon_path, 'wb') as f:
                f.write(icon_bytes)

            self.iconbitmap(default=temp_icon_path)

            def cleanup():
                try:
                    if os.path.exists(temp_icon_path):
                        os.remove(temp_icon_path)
                except:
                    pass

            self.protocol("WM_DELETE_WINDOW", lambda: [cleanup(), self.destroy()])

        except Exception as e:
            print(f"Не удалось загрузить иконку: {e}")


if __name__ == "__main__":
    app = VideoConverterApp()
    app.mainloop()