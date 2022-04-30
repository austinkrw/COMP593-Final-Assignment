""" 
COMP 593 - Final Project

Description: 
  Downloads NASA's Astronomy Picture of the Day (APOD) from a specified date
  and sets it as the desktop background image.

Usage:
  python apod_desktop.py image_dir_path [apod_date]

Parameters:
  image_dir_path = Full path of directory in which APOD image is stored
  apod_date = APOD image date (format: YYYY-MM-DD)
"""

from sys import argv, exit, getsizeof
from datetime import datetime, date
from xmlrpc.client import DateTime
from tkinter import image_names
from hashlib import sha256
from time import time
from os import path
import requests
import sqlite3
import ctypes
import sys
import os
import re

def main():

    # sets the path specified in argv1 to image_dir_path
    image_dir_path = get_image_dir_path()
    # crafts the path for the database
    db_path = path.join(image_dir_path, 'apod_images.db')
    # sets the date specified in argv2 to apod_date, if argv2 is not specified, the current date is used
    apod_date = get_apod_date()
    # create the images database if it does not already exist
    create_image_db(db_path)
    # retrieves a dictionary of information for a specific APOD date
    apod_info_dict = get_apod_info(apod_date)
    
    # set the image_url to either the APOD url or thumbnail url depending on if the APOD is a video or picture
    if "youtube.com" in apod_info_dict["url"]:
        image_url = apod_info_dict["thumbnail_url"]
    else:
        image_url = apod_info_dict["url"]
    # extracts the image name from the image url
    get_image_name = re.search(".*\/(.*)", image_url)
    image_name = get_image_name.group(1)
    # retrieves the image content
    image_msg = download_apod_image(image_url)
    # calculates the sha256 hash for the image data
    image_sha256 = sha256(image_msg).hexdigest()
    # calculates the size (in bytes) of the image data
    image_size = len(image_msg)#os.path.getsize(image_dir_path + "\\" + image_name)
    # retrieves path of where the image will be stored locally
    image_path = get_image_path(image_url, image_dir_path)

    # prints APOD information
    print_apod_info(image_url, image_path, image_size, image_sha256)
    # if the image is not already in the cache, save it to disk and add it to the database
    if not image_already_in_db(db_path, image_sha256):
        save_image_file(image_msg, image_path)
        add_image_to_db(db_path, image_path, image_size, image_sha256)
    # sets the desktop background image to the selected APOD
    set_desktop_background_image(image_path)

def get_image_dir_path():
    """
    Validates the command line parameter that specifies the path
    in which all downloaded images are saved locally.

    :returns: Path of directory in which images are saved locally
    """

    # returns and prints the path specified in argv1
    if len(argv) >= 2:
        dir_path = argv[1]
        if path.isdir(dir_path):
            print("Images directory:", dir_path)
            return dir_path
        else:
            print('Error: Non-existent directory', dir_path)
            exit('Script execution aborted')
    else:
        print('Error: Missing path parameter.')
        exit('Script execution aborted')

def get_apod_date():
    """
    Validates the command line parameter that specifies the APOD date.
    Aborts script execution if date format is invalid.

    :returns: APOD date as a string in 'YYYY-MM-DD' format
    """   

    if len(argv) >= 3:
        # date parameter has been provided, so get it
        apod_date = argv[2]

        # validate the date parameter format
        try:
            datetime.strptime(apod_date, '%Y-%m-%d')
        except ValueError:
            print('Error: Incorrect date format; Should be YYYY-MM-DD')
            exit('Script execution aborted')
    else:
        # no date parameter has been provided, so use today's date
        apod_date = date.today().isoformat()
    
    print("APOD date:", apod_date)
    return apod_date

def get_image_path(image_url, dir_path):
    """
    Determines the path at which an image downloaded from
    a specified URL is saved locally.

    :param image_url: URL of image
    :param dir_path: Path of directory in which image is saved locally
    :returns: Path at which image is saved locally
    """

    # extracts the image name from the image url
    get_img_name = re.search(".*\/(.*)", image_url)
    img_name = get_img_name.group(1)
    # crafts the path the image will be saved to
    path = (dir_path + "\\" + img_name)
    return path

def get_apod_info(date):
    """
    Gets information from the NASA API for the Astronomy 
    Picture of the Day (APOD) from a specified date.

    :param date: APOD date formatted as YYYY-MM-DD
    :returns: Dictionary of APOD info
    """    

    # sets apod_date to the second command line paramter, if not specified, use todays date
    if len(argv) >= 3:
        apod_date = argv[2]
    else:
        # the regular "date" class did not work here, I used a different method to get current date
        apod_date = sqlite3.Date.today().isoformat()

    # returns a dictionary containing information about the APOD date
    parameters = {"api_key": "2Dcnsp11pIh4C0XZMqKKpm12tMrtxQcPzX9ahrmS", "thumbs": "true", "date": apod_date}
    req = requests.get("https://api.nasa.gov/planetary/apod", params=parameters)
    apod_info = req.json()

    return apod_info

def print_apod_info(image_url, image_path, image_size, image_sha256):
    """
    Prints information about the APOD

    :param image_url: URL of image
    :param image_path: Path of the image file saved locally
    :param image_size: Size of image in bytes
    :param image_sha256: SHA-256 of image
    :returns: None
    """    

    print("Image URL: ", image_url)
    print("Image Path: ", image_path)
    print("Image Size: ", image_size, "bytes")
    print("Image Hash: ", image_sha256)

def download_apod_image(image_url):
    """
    Downloads an image from a specified URL.

    :param image_url: URL of image
    :returns: Response message that contains image data
    """
 
    # returns the image data
    img_data = requests.get(image_url).content

    return img_data

def save_image_file(image_msg, image_path):
    """
    Extracts an image file from an HTTP response message
    and saves the image file to disk.

    :param image_msg: HTTP response message
    :param image_path: Path to save image file
    :returns: None
    """

    # saves the image locally to image_path
    with open(image_path, "wb") as handler:
        handler.write(image_msg)

def create_image_db(db_path):
    """
    Creates an image database if it doesn't already exist.

    :param db_path: Path of .db file
    :returns: None
    """

    # if db_path does not lead to a valid file, create it, if it does, skip
    if os.path.isfile(db_path) == False:

        myConnection = sqlite3.connect(db_path)
        myCursor = myConnection.cursor()

        createIMAGEStable = """ CREATE TABLE IF NOT EXISTS images(
                            id integer PRIMARY KEY,
                            path text NOT NULL,
                            size text NOT NULL,
                            hash text NOT NULL,
                            date_downloaded text NOT NULL
                            );"""

        myCursor.execute(createIMAGEStable)
        myConnection.commit()
        myConnection.close()
    else:
        pass

def add_image_to_db(db_path, image_path, image_size, image_sha256):
    """
    Adds a specified APOD image to the DB.

    :param db_path: Path of .db file
    :param image_path: Path of the image file saved locally
    :param image_size: Size of image in bytes
    :param image_sha256: SHA-256 of image
    :returns: None
    """

    # crafts and executes a database query containing the image information
    myConnection = sqlite3.connect(db_path)
    myCursor = myConnection.cursor()

    query = """INSERT INTO images(
                path,
                size,
                hash,
                date_downloaded)
                VALUES (?, ?, ?, ?);"""

    addImg = (image_path,
            image_size,
            image_sha256,
            datetime.now())

    myCursor.execute(query, addImg)
    myConnection.commit()
    myConnection.close()

def image_already_in_db(db_path, image_sha256):
    """
    Determines whether the image in a response message is already present
    in the DB by comparing its SHA-256 to those in the DB.

    :param db_path: Path of .db file
    :param image_sha256: SHA-256 of image
    :returns: True if image is already in DB; False otherwise
    """ 

    # selects all image hashes that are equal to the current image hash
    myConnection = sqlite3.connect(db_path)
    myCursor = myConnection.cursor()

    myCursor.execute("""SELECT images.hash FROM images
            WHERE images.hash == (?)""",
            (image_sha256,))

    result = myCursor.fetchall()
    myConnection.commit()
    myConnection.close()

    # if the result returns nothing, there are no matching hashes, enables the picture to be added to the database
    if len(result) > 0:
        print("Image already exists...")
        return True
    else:
        print("Downloading image to the local filesystem...")
        return False

def set_desktop_background_image(image_path):
    """
    Changes the desktop wallpaper to a specific image.

    :param image_path: Path of image file
    :returns: None
    """

    # changes the desktop background to the picture of the APOD
    ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0)

main()