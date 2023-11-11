"""Some generic utility functions used in other modules"""

import logging
from datetime import datetime
from pathlib import Path
from PyQt5 import QtGui
import PIL.Image
import exifread

logging.getLogger("exifread").setLevel(logging.ERROR)

def app_dir(file):
    """"Return a file in the .app dir under  directory of the main script"""
    return Path( Path(__file__).parent.parent, '.app', file )

def app_icon(file):
    """"Return an icon in the .app dir"""
    icon_file = str(Path( Path(__file__).parent.parent, '.icons', file ))
    if Path(icon_file).is_file:
        found='yes'
    else:
        found= 'no'

    result = QtGui.QIcon( icon_file )

    isnull = 'no'
    if result.isNull():
        isnull = 'empty icon'

    logging.info('File %s found: %s isnull: %s', icon_file, found, isnull)
    return result

def image_taken_date(file):
    """Attempts to retrieve original date and time from a photo
    input: string or result of pathlib
    output: datetime object """

    # First try to return the file date and time using the exifread library
    try:
        f = open(file, 'rb')
        exif_data = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal')
        exif_datetime = exif_data['EXIF DateTimeOriginal']
        return datetime.strptime(exif_datetime.values, '%Y:%m:%d %H:%M:%S')
    except:
        #ToDo: catch specific exception in order not to catch system exit exception
        pass

    # If that did not work, try pillow
    try:
        img = PIL.Image.open(str(file))
        exif_data = img.getexif()
        exif_datetime = exif_data['EXIF DateTimeOriginal']
        datetime_str = f'{exif_datetime}'
        return datetime.strptime(datetime_str, '%Y:%m:%d %H:%M:%S')
    except:
        #ToDo: catch specific exception in order not to catch system exit exception
        pass

    # If that did also not work, report empty string
    return ""

def image_size(file):
    """Return the size (width,height) of the image in pixels"""

    # First try PIL since it is most likely installed on the computer
    logging.info("image_size called for %s", file)
    try:
        img = PIL.Image.open(file)
        return img.size
    except Exception as error:
        #ToDo: catch specific exception in order not to catch system exit exception
        logging.info('PIL error %s', error)

    # The use exifread since PIL may not work on ARW files
    try:
        f = open(file, 'rb')
        exifdata = exifread.process_file(f)
        width  = exifdata['EXIF ExifImageWidth' ].values[0]
        height = exifdata['EXIF ExifImageLength'].values[0]
        return (width, height)
    except:
        #ToDo: catch specific exception in order not to catch system exit exception
        return ("","")
