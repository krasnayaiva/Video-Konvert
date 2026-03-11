import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
from pathlib import Path
import shutil
import datetime

# Пытаемся импортировать библиотеки с проверкой
try:
    import cv2

    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from moviepy.editor import VideoFileClip

    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class VideoConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Konvert")
        self.root.geometry("650x550")

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.format_var = tk.StringVar(value="MP4")
        self.quality_var = tk.StringVar(value="medium")
        self.create_mpv_playlist = tk.BooleanVar(value=False)
        self.progress_var = tk.DoubleVar(value=0)

        """ Словарь соответствия форматов и расширений """
        self.format_extensions = {
            "MP4": "mp4",
            "AVI": "avi",
            "MOV": "mov",
            "MKV": "mkv",
            "WebM": "webm",
            "GIF": "gif",
            "MPV плейлист": "mpv",
            "3GP": "3gp",
            "FLV": "flv"
        }

        self.format_list = list(self.format_extensions.keys())

        self.check_libraries()
        self.create_widgets()

    def check_libraries(self):
        """Проверка наличия необходимых библиотек"""
        self.available_libs = []

        if OPENCV_AVAILABLE:
            self.available_libs.append("OpenCV")
        if MOVIEPY_AVAILABLE:
            self.available_libs.append("MoviePy")
        if PIL_AVAILABLE:
            self.available_libs.append("PIL")

        if not self.available_libs:
            messagebox.showerror(
                "Ошибка",
                "Не найдены библиотеки для работы с видео!\n\n"
                "Установите:\n"
                "pip install opencv-python\n"
                "pip install moviepy\n"
                "pip install pillow"
            )
            self.root.quit()

    def create_widgets(self):
        # Заголовок
        title_label = tk.Label(self.root,
                               text="Video Konvert",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Информация о доступных библиотеках
        libs_text = f"Доступные библиотеки: {', '.join(self.available_libs)}"
        tk.Label(self.root, text=libs_text, fg="green").pack()

        # Фрейм для выбора входного файла
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(input_frame, text="Входной файл:", width=12, anchor="w").pack(side="left")
        tk.Entry(input_frame, textvariable=self.input_path,
                 width=40).pack(side="left", padx=5)
        tk.Button(input_frame, text="Обзор",
                  command=self.select_input).pack(side="left")

        # Фрейм для выбора формата
        format_frame = tk.Frame(self.root)
        format_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(format_frame, text="Формат:", width=12, anchor="w").pack(side="left")

        self.format_combo = ttk.Combobox(format_frame,
                                         textvariable=self.format_var,
                                         values=self.format_list,
                                         width=25,
                                         state="readonly")
        self.format_combo.pack(side="left", padx=5)
        self.format_combo.bind('<<ComboboxSelected>>', self.on_format_change)

        # Выбор качества
        quality_frame = tk.Frame(self.root)
        quality_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(quality_frame, text="Качество:", width=12, anchor="w").pack(side="left")

        qualities = [("Макс.", "max"), ("Высокое", "high"),
                     ("Среднее", "medium"), ("Низкое", "low")]

        for text, value in qualities:
            tk.Radiobutton(quality_frame, text=text,
                           variable=self.quality_var,
                           value=value).pack(side="left", padx=5)

        # Опция для MPV плейлиста
        self.mpv_options_frame = tk.Frame(self.root)

        tk.Checkbutton(self.mpv_options_frame,
                       text="Создать MPV плейлист (для нескольких файлов)",
                       variable=self.create_mpv_playlist).pack(side="left", padx=5)

        # Информация о выходном файле
        output_frame = tk.Frame(self.root)
        output_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(output_frame, text="Выходной файл:", width=12, anchor="w").pack(side="left")
        self.output_label = tk.Label(output_frame, text="Будет создан автоматически",
                                     fg="blue", wraplength=400, anchor="w")
        self.output_label.pack(side="left", padx=5)

        # Кнопка для выбора папки сохранения
        folder_frame = tk.Frame(self.root)
        folder_frame.pack(pady=5, padx=10, fill="x")

        tk.Label(folder_frame, text="Папка:", width=12, anchor="w").pack(side="left")
        self.folder_label = tk.Label(folder_frame, text="Та же, что и исходный файл",
                                     fg="gray", anchor="w")
        self.folder_label.pack(side="left", padx=5)
        tk.Button(folder_frame, text="Изменить",
                  command=self.select_output_folder).pack(side="left", padx=5)

        # Информация о формате MPV
        self.mpv_info_label = tk.Label(self.root,
                                       text="",
                                       fg="blue", font=("Arial", 9))
        self.mpv_info_label.pack(pady=2)

        # Прогресс бар
        self.progress = ttk.Progressbar(self.root, variable=self.progress_var,
                                        maximum=100, length=550)
        self.progress.pack(pady=20)

        # Текстовое поле для логов
        log_frame = tk.Frame(self.root)
        log_frame.pack(pady=10, padx=10, fill="both", expand=True)

        tk.Label(log_frame, text="Лог операций:", anchor="w").pack(anchor="w")

        self.log_text = tk.Text(log_frame, height=5, width=70)
        self.log_text.pack(fill="both", expand=True)

        # Скроллбар для логов
        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)

        # Кнопка конвертации
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.convert_btn = tk.Button(button_frame, text="Конвертировать",
                                     command=self.start_conversion,
                                     bg="green", fg="white",
                                     font=("Arial", 12, "bold"),
                                     width=20)
        self.convert_btn.pack()

        # Статус
        self.status_label = tk.Label(self.root, text="Готов к работе",
                                     fg="blue")
        self.status_label.pack(pady=5)

        # Изначально скрываем MPV опции
        self.on_format_change()

    def on_format_change(self, event=None):
        """Обработчик изменения формата"""
        selected_format = self.format_var.get()

        if selected_format == "MPV плейлист":
            self.mpv_info_label.config(
                text="MPV формат: создает плейлист для проигрывателя mpv"
            )
            self.mpv_options_frame.pack(pady=5, padx=10, fill="x")
        else:
            self.mpv_info_label.config(text="")
            self.mpv_options_frame.pack_forget()
            self.create_mpv_playlist.set(False)

        self.update_output_path()

    def log(self, message):
        """Добавление сообщения в лог"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def select_input(self):
        filename = filedialog.askopenfilename(
            title="Выберите видеофайл",
            filetypes=[("Видео файлы", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.gif *.3gp"),
                       ("Все файлы", "*.*")]
        )
        if filename:
            self.input_path.set(filename)
            self.update_output_path()

    def select_output_folder(self):
        """Выбор папки для сохранения"""
        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if folder:
            self.folder_label.config(text=folder, fg="blue")
            self.custom_folder = folder
            self.update_output_path()

    def update_output_path(self):
        if not self.input_path.get():
            return

        input_file = Path(self.input_path.get())
        input_name = input_file.stem

        if hasattr(self, 'custom_folder') and self.custom_folder:
            output_dir = self.custom_folder
        else:
            output_dir = input_file.parent

        selected_format = self.format_var.get()
        format_ext = self.format_extensions.get(selected_format, "mp4")

        # Специальная обработка для MPV плейлиста
        if selected_format == "MPV плейлист" and self.create_mpv_playlist.get():
            output_filename = f"{input_name}_playlist.mpv"
        else:
            output_filename = f"{input_name}_converted.{format_ext}"

        output_path = Path(output_dir) / output_filename

        self.output_path.set(str(output_path))
        self.output_label.config(text=str(output_path))

    def start_conversion(self):
        if not self.input_path.get():
            messagebox.showerror("Ошибка", "Выберите входной файл!")
            return

        self.log_text.delete(1.0, tk.END)

        thread = threading.Thread(target=self.convert_video)
        thread.daemon = True
        thread.start()

    def create_mpv_playlist_file(self, input_path, output_path):
        """Создает MPV плейлист"""
        self.log("Создание MPV плейлиста...")

        video_files = []

        single_file = Path(input_path)
        video_files.append(single_file)

        if messagebox.askyesno("MPV плейлист",
                               "Хотите добавить другие видеофайлы в плейлист?"):
            more_files = filedialog.askopenfilenames(
                title="Выберите дополнительные видеофайлы",
                filetypes=[("Видео файлы", "*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv *.3gp")]
            )
            for f in more_files:
                video_files.append(Path(f))

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# MPV playlist\n")
            f.write(f"# Created by Video Converter\n")
            f.write(f"# Дата: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            for i, video in enumerate(video_files, 1):
                f.write(f"#{i}. {video.name}\n")
                f.write(f"{video.absolute()}\n\n")

        self.log(f"Создан плейлист с {len(video_files)} файлами")
        return True

    def convert_for_mpv(self, input_path, output_path):
        """Конвертирует видео для использования с MPV плеером"""
        self.log("Подготовка видео для MPV плеера...")

        temp_output = output_path.replace('.mpv', '_temp.mp4')

        if MOVIEPY_AVAILABLE:
            self.convert_with_moviepy(input_path, temp_output)
        elif OPENCV_AVAILABLE:
            self.convert_with_opencv(input_path, temp_output)

        if self.create_mpv_playlist.get():
            playlist_path = output_path
            self.create_mpv_playlist_file(temp_output, playlist_path)
            self.log(f"MPV плейлист создан: {playlist_path}")

            if messagebox.askyesno("MPV",
                                   "Сохранить также видеофайл?\n\n"
                                   "Да - сохранить видео отдельно\n"
                                   "Нет - удалить временный файл"):
                final_video = Path(output_path).parent / f"{Path(input_path).stem}_mpv_video.mp4"
                shutil.move(temp_output, final_video)
                self.log(f"Видео сохранено: {final_video}")
            else:
                os.remove(temp_output)
                self.log("Временный видеофайл удален")
        else:
            # Просто переименовываем .mp4 в .mpv
            if os.path.exists(output_path):
                os.remove(output_path)
            shutil.move(temp_output, output_path)
            self.log(f"Видео сохранено как MPV: {output_path}")

        return True

    def convert_with_opencv(self, input_path, output_path):
        """Конвертация видео с использованием OpenCV"""

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise Exception("Не удалось открыть видео")

        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.log(f"Видео: {width}x{height}, {fps} fps, {total_frames} кадров")

        fourcc_map = {
            ".mp4": cv2.VideoWriter_fourcc(*'mp4v'),
            ".avi": cv2.VideoWriter_fourcc(*'XVID'),
            ".mov": cv2.VideoWriter_fourcc(*'mp4v'),
            ".mkv": cv2.VideoWriter_fourcc(*'X264'),
            ".webm": cv2.VideoWriter_fourcc(*'VP80'),
            ".3gp": cv2.VideoWriter_fourcc(*'mp4v'),
            ".flv": cv2.VideoWriter_fourcc(*'FLV1')
        }

        ext = os.path.splitext(output_path)[1].lower()
        fourcc = fourcc_map.get(ext, cv2.VideoWriter_fourcc(*'mp4v'))

        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            out.write(frame)
            frame_count += 1

            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                self.progress_var.set(progress)
                self.root.update()

        cap.release()
        out.release()
        cv2.destroyAllWindows()

        self.log(f"Обработано {frame_count} кадров")

    def convert_with_moviepy(self, input_path, output_path):
        """Конвертация видео с использованием MoviePy"""
        clip = VideoFileClip(input_path)

        self.log(f"Видео: {clip.w}x{clip.h}, {clip.fps} fps, {clip.duration:.1f} сек")

        quality_bitrate = {
            "max": "8000k",
            "high": "5000k",
            "medium": "2500k",
            "low": "1000k"
        }

        bitrate = quality_bitrate.get(self.quality_var.get(), "2500k")

        ext = os.path.splitext(output_path)[1].lower()

        if ext == ".gif":
            self.log("Создание GIF...")
            clip = clip.resize(height=360)
            clip.write_gif(output_path, fps=10, logger=None)
        else:
            self.log("Конвертация видео...")
            videoclip = clip.without_audio()
            videoclip.write_videofile(
                output_path,
                codec='libx264',
                bitrate=bitrate,
                preset='medium',
                logger=None
            )
            videoclip.close()

        clip.close()

    def convert_video(self):
        try:
            self.convert_btn.config(state="disabled")
            self.status_label.config(text="Конвертация...", fg="orange")
            self.progress_var.set(0)

            input_path = self.input_path.get()
            output_path = self.output_path.get()
            selected_format = self.format_var.get()

            self.log(f"Начало конвертации:")
            self.log(f"Входной файл: {input_path}")
            self.log(f"Выходной файл: {output_path}")
            self.log(f"Целевой формат: {selected_format}")

            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Файл не найден: {input_path}")

            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            if selected_format == "MPV плейлист":
                self.convert_for_mpv(input_path, output_path)
            elif MOVIEPY_AVAILABLE:
                self.convert_with_moviepy(input_path, output_path)
            elif OPENCV_AVAILABLE:
                self.convert_with_opencv(input_path, output_path)
            else:
                raise Exception("Нет доступных библиотек для конвертации")

            self.progress_var.set(100)

            if os.path.exists(output_path) or (selected_format == "MPV плейлист" and os.path.exists(output_path)):
                file_size = 0
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path) / (1024 * 1024)

                self.status_label.config(
                    text=f"Готово! Размер: {file_size:.2f} МБ" if file_size > 0 else "Готово!",
                    fg="green"
                )
                self.log(f"\n✅ Конвертация успешно завершена!")
                if file_size > 0:
                    self.log(f"Размер файла: {file_size:.2f} МБ")

                messagebox.showinfo("Успех",
                                    f"Конвертация завершена!\n\n"
                                    f"Сохранено: {output_path}")
            else:
                raise Exception("Выходной файл не создан")

        except Exception as e:
            self.progress_var.set(0)
            self.status_label.config(text="Ошибка", fg="red")
            self.log(f"\n❌ Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", str(e))

        finally:
            self.convert_btn.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoConverterApp(root)
    root.mainloop()