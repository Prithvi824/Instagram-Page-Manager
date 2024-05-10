import os
import dotenv
from typing import List
from moviepy.config import change_settings
from moviepy.editor import VideoFileClip, clips_array, TextClip

dotenv.load_dotenv()

# Change this path to your ImageMagick installation path
change_settings({"IMAGEMAGICK_BINARY": os.getenv("IMAGEMAGICK_BINARY")})

def split_and_create_thumbnail(video_file: str, start_part: int, part_duration: int = 60, start_time: int = 10, end_skip: int = 20) -> List[str]:
    """
    `video_file`: The path to the big video

    `start_part`: The starting number of part

    `part_duration`: The duration of each part

    `start_time`: Time to skip from the start

    `end_skip`: Time to skip from the end

    `Return:` A list of all the parts location
    """

    # Create a directory to save the small videos
    if not os.path.exists("small_videos"):
        os.makedirs("small_videos")

    # Load the main video
    main_video = VideoFileClip(video_file)
    duration = main_video.duration

    # Exclude the first and last 10 seconds
    end_time = duration - end_skip

    parts = int((end_time - start_time) / part_duration)
    parts += 1 if (end_time - start_time) % part_duration > 0 else 0

    # Array to contain all the paths of the small videos
    paths = []

    for i in range(parts):
        part_start_time = start_time + i * part_duration
        part_end_time = min(start_time + (i + 1) * part_duration, end_time)

        # Extract the part of the video
        part_video = main_video.subclip(part_start_time, part_end_time)
        part_video = part_video.volumex(1.25)

        # Create a black image with text
        black_clip = TextClip(f"PART {start_part + i}", fontsize=70, font="Caladea", color='white')
        black_clip = black_clip.set_duration(part_video.duration)
        black_clip = black_clip.set_position(('center', 'top'))

        # Combine the black clip and the part video
        combined_clip = clips_array([
            [black_clip],
            [part_video]
        ])

        # Save the combined clip
        combined_clip.write_videofile(f"small_videos/part_{start_part + i}.mp4", codec='libx264', audio_codec='aac', fps=24)
        paths.append(os.path.join(os.getcwd(), f"small_videos\\part_{start_part + i}.mp4"))

    # Close the main video
    main_video.close()
    return paths
