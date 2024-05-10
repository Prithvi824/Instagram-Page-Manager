import os
import re
from pytube import YouTube

class Yt:
    def __init__(self, url: str, directory: str | None = None) -> None:
        """
        A Yt instance of a video with function to download it easily
        """
        self.video: YouTube = YouTube(url)
        self.directory = os.path.join(os.getcwd(), "video") if not directory else os.path.join(os.getcwd(), directory)

    def download_video(self, name: str | None = None) -> str:
        """
        name: The name of the file to store with the extension        
        """
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

        def clean_filename(filename):
            """
            cleans the filename to avoid potential errors
            """
            cleaned_filename = re.sub(r'[\\/*?:"<>|]', "", filename)
            return cleaned_filename

        filename = clean_filename(self.video.title) + ".mp4" if not name else clean_filename(name)

        return self.video.streams.get_by_itag("18").download(self.directory, filename)

    def get_info(self):
        print("self.directory: ", self.directory)
        print("self.video: ", self.video.watch_url)
