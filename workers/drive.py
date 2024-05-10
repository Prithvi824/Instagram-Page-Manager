import os
import random
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

class DriveHandler:
    """
    Represents the drive object with custom functions and operations
    """

    def __init__(self, creds_file, folder_id):
        """
        @param creds_file: The name of the credentials file
        @param folder_id: The parent folder Id to interact with
        """

        # A variable to keep track of downloads
        self.COUNT = 30

        # Initializes the authentication
        creds = Credentials.from_service_account_file(creds_file, scopes=['https://www.googleapis.com/auth/drive'])
        self.drive = build('drive', 'v3', credentials=creds)
        self.folder_id = folder_id

    def upload(self, file, file_type, file_name):
        """
        Uploads a file to drive

        => file: The path of the file to upload
        => type: The type of the file
        => file_name: The name of file to store on drive

        `returns`: The id of the uploaded file
        """
        file_metadata = {'name': file_name, 'parents': [self.folder_id]}
        media = MediaFileUpload(file, mimetype=file_type, resumable=True)
        file = self.drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id', None)
    
    def get_download_link(self, file_id):
        """
        Creates a downloadable link of a file
        => file_id: The id of the file of which link should be generated
        `returns` The download link of the file
        """
        # Change the permission to be available to anyone
        self.drive.permissions().create(fileId=file_id, body={'type': 'anyone', 'role': 'reader'}).execute()

        # Create the download link
        result = self.drive.files().get(fileId=file_id, fields='webContentLink').execute()

        # Return the download link
        return result.get('webContentLink')

    def get_list(self):
        """
        To get the list of all the files and folders in the specified drive folder.
        
        @returns a list containing objects with `kind`, `mimeType`, `id`, `name` keys of each file/folder
        """
        files = []
        page_token = None

        while True:
            response = self.drive.files().list(q=f"'{self.folder_id}' in parents and trashed=false",
                                            fields="nextPageToken, files(kind, mimeType, id, name)",
                                            pageToken=page_token).execute()
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        return files

    def pick_one(self):
        """
        Used to pick a random file from drive
        @returns a random file object `kind`, `mimeType`, `id`, `name` keys
        """
        files = self.get_list()
        random_file = random.choice(files)
        return random_file

    def delete_one(self, file_id):
        """
        Deletes a file from drive based on its id
        @param file_id
        @returns {null}
        """
        self.drive.files().delete(fileId=file_id).execute()
        return None
