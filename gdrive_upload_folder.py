# -*- coding: utf-8 -*-

# Adpted code from: https://gist.github.com/jmlrt/f524e1a45205a0b9f169eb713a223330

"""
    Upload folder to Google Drive
"""

# Enable Python3 compatibility
from __future__ import (unicode_literals, absolute_import, print_function,
                        division)

# Import Google libraries
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials
from pydrive.files import GoogleDriveFileList
import googleapiclient.errors

# Import general libraries
from argparse import ArgumentParser
from os import chdir, listdir, stat, path
from sys import exit
import ast


def authenticate():
    """ 
        Authenticate to Google API
    """
    auth.authenticate_user()
    gauth = GoogleAuth()
    gauth.credentials = GoogleCredentials.get_application_default()
    drive = GoogleDrive(gauth)

    return drive


def get_folder_id(drive, parent_folder_id, folder_name):
    """ 
        Check if destination folder exists and return it's ID
    """
    print("PARENT FOLDER ID: {0} | FOLDER NAME: {1}".format(parent_folder_id,folder_name))
    

    # Auto-iterate through all files in the parent folder.
    file_list = GoogleDriveFileList()
    print(file_list)
    try:
        file_list = drive.ListFile(
            {'q': "'{0}' in parents and trashed=false".format(parent_folder_id)}
        ).GetList()
    # Exit if the parent folder doesn't exist
    except googleapiclient.errors.HttpError as err:
        # Parse error message
        message = ast.literal_eval(err.content)['error']['message']
        if message == 'File not found: ':
            print(message + folder_name)
            exit(1)
        # Exit with stacktrace in case of other error
        else:
            raise

    # Find the the destination folder in the parent folder's files
    for file1 in file_list:
        if file1['title'] == folder_name:
            print('title: %s, id: %s' % (file1['title'], file1['id']))
            return file1['id']


def create_folder(drive, folder_name, parent_folder_id):
    """ 
        Create folder on Google Drive
    """
    
    folder_metadata = {
        'title': folder_name,
        # Define the file type as folder
        'mimeType': 'application/vnd.google-apps.folder',
        # ID of the parent folder        
        'parents': [{"kind": "drive#fileLink", "id": parent_folder_id}]
    }

    folder = drive.CreateFile(folder_metadata)
    folder.Upload()

    # Return folder informations
    print("title: {0}, id: {1}".format(folder['title'], folder['id']))
    return folder['id']


def upload_files(drive, folder_id, src_folder_name, dst_folder_name, parent_folder_name):
    """ 
        Upload files in the local folder to Google Drive 
    """

    # Enter the source folder
    try:
        chdir(src_folder_name)
    # Print error if source folder doesn't exist
    except OSError:
        print(src_folder_name + 'is missing')
    # Auto-iterate through all files in the folder.
    for file1 in listdir('.'):
        # Check the file's size
        statinfo = stat(file1)
        if statinfo.st_size > 0:
            if path.isfile(file1):
                print('uploading file ' + file1)
                # Upload file to folder.
                f = drive.CreateFile(
                    {"parents": [{"kind": "drive#fileLink", "id": folder_id}]})
                f.SetContentFile(file1)
                f.Upload()
            elif path.isdir(file1):
                print('uploading folder ' + file1)
                upload(file1,folder_id,file1,dst_folder_name)
        # Skip the file if it's empty
        else:
            print('file {0} is empty'.format(file1))
            
def upload(src_folder_name,parent_folder_id,dst_folder_name,parent_folder_name):
    drive = authenticate()
    
    # Get destination folder ID
    folder_id = get_folder_id(drive, parent_folder_id, dst_folder_name)
    # Create the folder if it doesn't exists
    if not folder_id:
        print('creating folder ' + dst_folder_name)
        folder_id = create_folder(drive, dst_folder_name, parent_folder_id)
    else:
        print('folder {0} already exists'.format(dst_folder_name))

    # Upload the files    
    upload_files(drive, folder_id, src_folder_name, dst_folder_name, parent_folder_name)

def upload_folder(src_folder_name, dst_folder_name, parent_folder_name='Colab Notebooks', root='root'):
    """ 
        Upload Folder

        Keyword arguments:
        src_folder_name -- Folder to upload
        src_folder_name -- Destination Folder in Google Drive
        parent_folder_name -- Parent Folder in Google Drive
    """

    # Authenticate to Google API
    drive = authenticate()
    # Get parent folder ID
    parent_folder_id = get_folder_id(drive, root, parent_folder_name)
    # Get destination folder ID
    folder_id = get_folder_id(drive, parent_folder_id, dst_folder_name)
    # Create the folder if it doesn't exists
    if not folder_id:
        print('creating folder ' + dst_folder_name)
        folder_id = create_folder(drive, dst_folder_name, parent_folder_id)
    else:
        print('folder {0} already exists'.format(dst_folder_name))

    # Upload the files    
    upload_files(drive, folder_id, src_folder_name, dst_folder_name, parent_folder_name)