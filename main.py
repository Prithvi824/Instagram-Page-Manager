# Import dependencies
import os
import random
import logging
import requests
import urllib.parse
from database import MongoDb
from workers.drive import DriveHandler
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

# Load env
import dotenv
dotenv.load_dotenv()

# Initialize variables
TOKEN = os.getenv('TOKEN')
FILTER = {'page': "beyblade"}
PAGE_ID = os.getenv('PAGE_ID')
COLLECTION = os.getenv("COLLECTION")
PARENT_FOLDER = os.getenv("PARENT_FOLDER")

# Initialize instances
DRIVE = DriveHandler("creds.json", PARENT_FOLDER)
DATABASE = MongoDb(os.getenv("MONGO"), os.getenv("DATABASE"))

captions = ["🌀 Beyblade Metal Fusion! 🌀 Let the battle begin! #Beyblade #BeybladeBlast #OldCartoons #Nostalgia #ClassicCartoons",
                "⚔️ Let it rip! ⚔️ Dive into nostalgia with Beyblade! Who's your favorite Blader? #Beyblade #LetItRip #NostalgiaTrip #ClassicCartoons #OldSchoolAnime",
                "💥 It's time to Beyblade! 💥 Relive the excitement of spinning tops and epic battles! #Beyblade #SpinningTops #ClassicAnime #NostalgiaTrip #CartoonClassics"]

# Logger settings
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)

def create_container(token, page_id, video_url, caption):
    """
    Create a container for the reel on Instagram.
    """
    container_url = f"https://graph.facebook.com/v19.0/{page_id}/media?video_url={video_url}&caption={caption}&media_type=REELS&access_token={token}"
    response = requests.post(container_url)

    if response.status_code == 200:
        container_id = response.json()["id"]
        return container_id

def check_container_status(container_id, token):
    """
    Check if the container is ready to be published.
    """
    status_url = f"https://graph.facebook.com/v19.0/{container_id}?fields=status_code&access_token={token}"
    response = requests.get(status_url)

    if response.status_code == 200:
        status = response.json()["status_code"]
        return status
    return None

def publish_container(page_id, container_id, token):
    """
    Publish the reel if ready.
    """
    status = check_container_status(container_id, token)
    if status == "FINISHED":
        publish_url = f"https://graph.facebook.com/v19.0/{page_id}/media_publish?creation_id={container_id}&access_token={token}"
        response = requests.post(publish_url)
        return bool(response.json().get("id"))
    elif status == "IN_PROGRESS":
        return False
    elif status == "PUBLISHED":
        return True
    else:
        # Load the json data
        json_data = DATABASE.get_document(COLLECTION, FILTER)

        # Create a new container and discard all old containers
        item = json_data["pendingPublish"][0]
        new_container = create_container(TOKEN, PAGE_ID, DRIVE.get_download_link(item["file_id"]), urllib.parse.quote(random.choice(captions)))

        # Upodate the database
        response = DATABASE.update_document(COLLECTION, FILTER, {"$set": {"pendingPublish": [{"file_id": item["file_id"], "insta_id": new_container}]}})
        logger.info(f"An Error occured with the container. Status code: {status}, so a new container was created with id: {new_container}, Data updatain code: {response}")
        return False

def create_container_job():
    """
    Cron job to create a container.
    """

    logger.info("Cron job running to create a container.")

    # Load the file list
    files = DRIVE.get_list()

    # Load the json data
    json_data = DATABASE.get_document(COLLECTION, FILTER)
    current_upload = json_data["lastUploaded"] + 1

    logger.info(f"Json Data loaded finding part_{current_upload}.mp4 in drive.")

    # Find the file which has to be uploaded serially
    current_file = None
    for item in files:
        if item["name"] == f"part_{current_upload}.mp4":
            current_file = item
            break

    # If no such file exists return
    if not current_file:
        logger.info(f"No File found quitting, last reel: ep{current_upload - 1}")
        return
    logger.info(f"File found creating a container for: part_{current_upload}.mp4")

    # Get the download link of the video to be uploaded and create a container
    link = DRIVE.get_download_link(current_file["id"])
    media_id = create_container(TOKEN, PAGE_ID, link, urllib.parse.quote(random.choice(captions)))

    # Update the Json with the pending publish
    json_data["pendingPublish"].append({"file_id": current_file["id"], "insta_id": media_id})
    response = DATABASE.replace_document(COLLECTION, FILTER, json_data)

    logger.info(f"Container created succesfully. The Container Id: {media_id}. Data update code: {response}")

def publish_container_job():
    """
    Cron job to publish a container every 30 minutes.
    """
    logger.info("Cron job running to publish a container.")

    # Load the json data
    json_data = DATABASE.get_document(COLLECTION, FILTER)

    # Check for a container
    if len(json_data["pendingPublish"]) == 0:
        logger.info("No Container detected exiting Job.")
        return

    item = json_data["pendingPublish"][0]
    logger.info(f"Container with id: {item['insta_id']} detected trying to publish.")

    # Publish the container
    res = publish_container(PAGE_ID, item["insta_id"], TOKEN)
    if res:
        response_publish = DATABASE.update_document(COLLECTION, FILTER, {"$pop": {"pendingPublish": -1}})
        response_lastUpload = DATABASE.update_document(COLLECTION, FILTER, {"$inc": {"lastUploaded": 1}})
        deleted_status = DRIVE.delete_one(item["file_id"])
        logger.info(f"Container was published succesfully. Data updatation boolean: {bool(response_lastUpload and response_publish)}, Drive status: {deleted_status}")

    else:
        logger.info("Container was not published.")

scheduler = BackgroundScheduler()
scheduler.add_job(create_container_job, 'cron', minute=f"30")
scheduler.add_job(publish_container_job, 'cron', minute=f"40")

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/fetch', methods=['GET'])
def get_json():
    json_data = DATABASE.get_document(COLLECTION, FILTER)
    data = {}

    for key, value in json_data.items():
        if key != "_id":
            data[key] = value
    return data

@app.route('/upload', methods=['POST'])
def upload_json():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data received'})

    response = DATABASE.replace_document(COLLECTION, FILTER, data)

    if response:
        return jsonify({'message': 'JSON data successfully uploaded', "updatedDoc": data})
    return jsonify({'message': 'some error occured'})

if __name__ == "__main__":
    scheduler.start()
    app.run(host="0.0.0.0",port=10000)
