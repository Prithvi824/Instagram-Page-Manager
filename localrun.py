import json
import os
import time
import dotenv
import logging
from database import MongoDb
from workers.downloader import Yt
from workers.drive import DriveHandler
from workers.editor import split_and_create_thumbnail

dotenv.load_dotenv()
FILTER = {'page': "beyblade"}
COLLECTION = os.getenv("COLLECTION")
DATABASE = MongoDb(os.getenv("MONGO"), os.getenv("DATABASE"))

PARENT_FOLDER = os.getenv("PARENT_FOLDER")
DRIVE = DriveHandler("creds.json", PARENT_FOLDER)

def midnight_cron():
    """
    The work of this cron job is to download a Yt video 
    and then edit it and create sub parts after that upload it to the drive.

    This basically handles the editor and uploader
    """

    logger.info("Midnight cron job running.")
    
    # Load the json data
    json_data = DATABASE.get_document(COLLECTION, FILTER)

    # Extract neccessary info
    links = json_data["links"]
    last_part = json_data["lastUsed"]
    lastReelPart = json_data["lastReelPart"]

    # Download the youtube video
    Yt_obj = Yt(links[f"ep{last_part + 1}"])
    path = Yt_obj.download_video()

    # Create short reels with the text and then delete main video
    reels = split_and_create_thumbnail(path, lastReelPart + 1)
    os.remove(path)

    upload_ind = 0

    # Upload each reel and delete them simultaneously
    for reel in reels:
        result = DRIVE.upload(reel, "video/mp4", os.path.basename(reel))
        if result:
            os.remove(reel)
            upload_ind += 1

    # Update the json data and write it in file
    response_lastUsed = DATABASE.update_document(COLLECTION, FILTER, {"$inc": {"lastUsed": 1}})
    response_lastUpload = DATABASE.update_document(COLLECTION, FILTER, {"$inc": {"lastReelPart": len(reels)}})

    logger.info(f"One episode completed, Data updatation bool: {response_lastUsed and response_lastUpload}\n")

# Logger settings
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)

for i in range(2):
    t1 = time.time()
    midnight_cron()
    logger.info(f"Time Taken: {time.time() - t1}\n\n")