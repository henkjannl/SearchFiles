import logging
from pathlib import Path
from PyQt5 import QtGui, QtCore, QtWidgets

logging.getLogger("exifread").setLevel(logging.ERROR)

def app_dir(file):
    """"Return a file in the .app dir under  directory of the main script"""
    return Path( Path(__file__).parent.parent, '.app', file )

def app_icon(file):
    """"Return an icon in the .app dir"""
    icon_file = str(Path( Path(__file__).parent.parent, '.icons', file ))
    return QtGui.QIcon( icon_file )


def image_taken_date(file):
    """Attempts to retrieve original date and time from a photo
    input: string or result of pathlib
    output: datetime object """
    from datetime import datetime

    # First try to return the file date and time using the exifread library
    try:
        import exifread
        f = open(file, 'rb')
        exif_data = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal')
        exif_datetime = exif_data['EXIF DateTimeOriginal']
        return datetime.strptime(exif_datetime.values, '%Y:%m:%d %H:%M:%S')
    except: 
        pass
    
    # If that did not work, try pillow
    try:
        import PIL.Image
        img = PIL.Image.open(str(file))
        exif_data = img.getexif()
        exif_datetime = exif_data['EXIF DateTimeOriginal']
        datetime_str = f'{exif_datetime}'
        return datetime.strptime(datetime_str, '%Y:%m:%d %H:%M:%S')
    except:
        pass

    # If that did also not work, report empty string
    return ""

def image_size(file):
    # First try PIL since it is most likely installed on the computer
    logging.info(f"image_size called for {file}")
    try:
        import PIL.Image
        img = PIL.Image.open(file)
        return img.size
    except Exception as error:
        logging.info(f'PIL error {error}')
    
    # The use exifread since PIL may not work on ARW files
    try:
        import exifread
        f = open(file, 'rb')
        exifdata = exifread.process_file(f)
        width = exifdata['EXIF ExifImageWidth'].values[0]
        height = exifdata['EXIF ExifImageLength'].values[0]
        return (width, height)
    except:
        return ("","")
