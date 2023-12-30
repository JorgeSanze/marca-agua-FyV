import os
import time
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import moviepy.editor as mp
from moviepy.audio.fx.all import audio_fadeout
import concurrent.futures


class Watermarker(FileSystemEventHandler):
    def __init__(self, folder_path, folder_target, watermark_file, watermark_size_percent_horizontal, watermark_size_percent_vertical, max_workers=2):
        super().__init__()
        self.folder_path = folder_path
        self.folder_target = folder_target
        self.watermark_file = watermark_file
        self.watermark_size_percent_horizontal = watermark_size_percent_horizontal
        self.watermark_size_percent_vertical = watermark_size_percent_vertical
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

        self.process_existing_files()

    def process_existing_files(self):
        if not os.path.exists(self.folder_path):
            raise FileNotFoundError(f"La carpeta {self.folder_path} no existe.")

        os.makedirs(self.folder_target, exist_ok=True)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for filename in os.listdir(self.folder_path):
                if self.is_valid_video(filename):
                    executor.submit(self.process_video, os.path.join(self.folder_path, filename))

    def is_valid_video(self, filename):
        return filename.lower().endswith((".mp4", ".avi", ".mov"))

    def process_video(self, video_path):
        filename = os.path.basename(video_path)
        clip = mp.VideoFileClip(video_path)
        audio_clip = clip.audio
        
        width, height = clip.size

        is_vertical = height > width

        if is_vertical:
            watermark_size_percent = self.watermark_size_percent_vertical
            new_size = (720, 1080)
        else:
            watermark_size_percent = self.watermark_size_percent_horizontal
            new_size = (1080, 720)

        if new_size:
            clip = clip.resize(new_size)
            
        watermark = (mp.ImageClip(self.watermark_file)
                    .set_duration(clip.duration)
                    .resize(height=clip.h * watermark_size_percent)
                    .margin(right=1, top=1, opacity=0)
                    .set_pos(("center")))
        
        video_with_watermark = mp.CompositeVideoClip([clip, watermark])
        final_clip = video_with_watermark.set_audio(audio_clip)
        final_clip = final_clip.fx(audio_fadeout, 0.5) 
        
        video_with_watermark_path = os.path.join(self.folder_target, "ma_" + filename)
        final_clip.write_videofile(video_with_watermark_path, codec='libx264', audio_codec='aac')

    def on_created(self, event):
        if event.is_directory:
            return

        if self.is_valid_video(event.src_path):
            self.executor.submit(self.process_video, event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return

        if self.is_valid_video(event.src_path):
            self.executor.submit(self.process_video, event.src_path)

if __name__ == "__main__":
    folder_path = "/Users/yorch/fotos"
    folder_target = "/Users/yorch/fotos-marca"
    watermark_file = "/Users/yorch/marca-agua-50.png"
    watermark_size_percent_horizontal = 0.45
    watermark_size_percent_vertical = 0.2

    watermarker = Watermarker(folder_path, folder_target, watermark_file, watermark_size_percent_horizontal, watermark_size_percent_vertical, max_workers=2)

    observer = Observer()
    observer.schedule(watermarker, folder_path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


#Este script necesita de las biliotecas: openCV,Pillow,Watchdog y moviepy.