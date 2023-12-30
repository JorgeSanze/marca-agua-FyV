import os
import time
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Watermarker(FileSystemEventHandler):
    def __init__(self, folder_path, folder_target, watermark_file, watermark_size_percent):
        super().__init__()
        self.folder_path = folder_path
        self.folder_target = folder_target
        self.watermark_file = watermark_file
        self.watermark_size_percent = watermark_size_percent

        self.process_existing_images()

    def process_existing_images(self):
        if not os.path.exists(self.folder_path):
            raise FileNotFoundError(f"La carpeta {self.folder_path} no existe.")

        os.makedirs(self.folder_target, exist_ok=True)

        for filename in os.listdir(self.folder_path):
            if self.is_valid_image(filename):
                self.process_image(os.path.join(self.folder_path, filename))

    def is_valid_image(self, filename):
        return filename.lower().endswith((".jpg", ".jpeg", ".png"))

    def process_image(self, image_path):
        filename = os.path.basename(image_path)
        with Image.open(image_path) as image, Image.open(self.watermark_file) as watermark:
            watermark_size = (int(image.size[0] * self.watermark_size_percent), int(image.size[1] * self.watermark_size_percent))
            watermark_resized = watermark.copy()
            watermark_resized.thumbnail(watermark_size)

            watermark_position = ((image.size[0] - watermark_resized.size[0]) // 2, (image.size[1] - watermark_resized.size[1]) // 2)
            image.paste(watermark_resized, watermark_position, watermark_resized)

            image_with_watermark_path = os.path.join(self.folder_target, "ma_" + filename)
            image.save(image_with_watermark_path)

    def on_created(self, event):
        if event.is_directory or not self.is_valid_image(event.src_path):
            return

        self.process_image(event.src_path)

    def on_modified(self, event):
        if event.is_directory or not self.is_valid_image(event.src_path):
            return

        self.process_image(event.src_path)


if __name__ == "__main__":
    folder_path = "/Users/yorch/fotos"
    folder_target = "/Users/yorch/fotos-marca"
    watermark_file = "/Users/yorch/marca-agua-50.png"
    watermark_size_percent = 0.6

    watermarker = Watermarker(folder_path, folder_target, watermark_file, watermark_size_percent)

    observer = Observer()
    observer.schedule(watermarker, folder_path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
