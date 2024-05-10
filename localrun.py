import json
import os
import time
import dotenv
import logging

from workers.downloader import Yt
from workers.drive import DriveHandler

dotenv.load_dotenv()

PARENT_FOLDER = os.getenv("PARENT_FOLDER")
DRIVE = DriveHandler("creds.json", PARENT_FOLDER)

def midnight_cron():
    """
    The work of this cron job is to download a Yt video 
    and then edit it and create sub parts after that upload it to the drive.

    This basically handles the editor and uploader
    """

    logger.info("Midnight cron job running.")
    # Load the data from the json file
    with open("info.json", "r+") as file:
        json_data = json.load(file)

    # Extract neccessary info
    links = json_data["links"]
    last_part = json_data["lastUsed"]
    lastReelPart = json_data["lastReelPart"]

    logger.info(f"The last episode used: {last_part}")
    logger.info(f"The episode which will be used: ep{last_part + 1}")
    logger.info(f"The last Reel part created: {lastReelPart}")

    # Download the youtube video
    Yt_obj = Yt(links[f"ep{last_part + 1}"])
    path = Yt_obj.download_video()

    logger.info(f"The episode was downloaded from Youtube.")
    logger.info(f"Downloaded path: {path}")

    # Create short reels with the text and then delete main video
    reels = split_and_create_thumbnail(path, lastReelPart + 1)
    os.remove(path)

    logger.info(f"The video was splitted into {len(reels)} parts")
    upload_ind = 0

    # Upload each reel and delete them simultaneously
    for reel in reels:
        result = DRIVE.upload(reel, "video/mp4", os.path.basename(reel))
        if result:
            os.remove(reel)
            upload_ind += 1

    logger.info(f"Toatal {upload_ind} was uploaded to drive.")
    logger.info(f"Last part: {reels[-1]}")

    # Update the json data and write it in file
    json_data["lastUsed"] += 1
    json_data["lastReelPart"] += len(reels)
    with open("info.json", "w") as file:
        json.dump(json_data, file)

# Logger settings
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)

for i in range(10):
    t1 = time.time()
    midnight_cron()
    logger.info(f"Time Taken: {time.time() - t1}")