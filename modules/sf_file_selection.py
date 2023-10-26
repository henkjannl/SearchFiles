import logging
from datetime import datetime
from pathlib import Path
from PyQt5 import QtCore
import pyperclip

from modules.sf_constants import *
from modules.sf_utilities import *

# This object sits in the parallel thread that moves files from camera to computer
class Selected_File(QtCore.QObject):
    """File to be moved from camera to harddisk"""

    def __init__(self, identifier, root, entry):
        """Create new standard item with file info
        The identifier is needed to link a file in the GUI to a file in the list.
        If a file in the list is directly displayed in the GUI, a multithreading problem occurs"""
        # Call initializer of QStandardItem
        super().__init__()

        self.identifier = identifier
        self.entry = entry
        self.image_size = None
        self.parents = entry.relative_to(root).parts[:-1]
        logging.info(f"File {entry.name}")

    def file_size(self): 
        """File size of the photo"""
        return self.entry.stat().st_size
    
    def created(self):
        return datetime.fromtimestamp(self.entry.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')
    
    def modified(self):
        return datetime.fromtimestamp(self.entry.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')

    def accessed(self):
        return datetime.fromtimestamp(self.entry.stat().st_atime).strftime('%Y-%m-%d %H:%M:%S')

    def directory(self):
        """Directory in which the file resides"""
        return str(self.entry.parent)
    
    def full_path(self):
        return str(self.entry.resolve() )
    
    def image_width(self):
        if self.image_size==None:
            self.image_size = image_size(self.entry)

        return self.image_size[0]

    def image_height(self):
        if self.image_size==None:
            self.image_size = image_size(self.entry)

        return self.image_size[0]

    def field(self, field):
        if field==COL_PATH:
            return self.directory()
        elif field==COL_FILE_NAME:
            return self.entry.name
        elif field==COL_FILE_SIZE:
            return self.file_size()
        elif field==COL_PATH_AND_NAME:
            return self.full_path()
        elif field==COL_CREATE_DATE:
            return self.created()
        elif field==COL_MODIFIED_DATE:
            return self.modified()
        elif field==COL_ACCESSED_DATE:
            return self.accessed()
        elif field==COL_IMAGE_TAKEN_DATE:
            return image_taken_date(self.entry)
        elif field==COL_IMAGE_WIDTH:
            return self.image_width()
        elif field==COL_IMAGE_HEIGHT:
            return self.image_height()
        else:
            return "Invalid field"
    
class File_Selection(QtCore.QObject):
    """Creates list of photos on camera and function that moves them to harddisk"""

    def __init__(self):
        """Initialize the the file selection list object
        The unique identifier is needed to link a file in the GUI to a file in the list.
        If a file in the list is directly displayed in the GUI, a multithreading problem occurs"""
        super().__init__(None)
        self.unique_identifier = 0
        self.filter_extension = ''
        self.filter_filename = ''
        self.selected_files = {}

    def select_files(self, root_directory, filter_extension, filter_filename):
        """Look in various places for the camera and search for suitable files"""
        self.unique_identifier = 0
        self.selected_files = []
        self.root_directory = Path(root_directory)
        self.filter_extension = filter_extension
        self.filter_filename = filter_filename
        logging.info(f"select_files called for {root_directory} containing {filter_filename} with extension {filter_extension}")

        self.__add_to_selection__( Path(root_directory) )

        # Sort files, directories first, then sort on filename
        #self.selected_files.sort( key= lambda selected_file: (-len(selected_file.entry.parts), str(selected_file.entry.name.lower() ) ) )
        self.selected_files.sort( key= lambda selected_file: (selected_file.entry.is_dir(), str(selected_file.full_path() ) ) )
        logging.info(f"{len(self.selected_files)} photo's found")

    def requirement(self, entry):
        """Filter the files that were found
        Override this member to make a different selection"""

        # Do not select directories
        if entry.is_dir():
            return False
        
        # Do not select if extension requirement is not met
        # ToDo: compare actual extension, instead of endswith
        # ToDo: ensure filter '' is still selecting all files
        if not entry.name.lower().endswith(self.filter_extension):
            return False

        # Do not select if filename filter requirement is not met
        if not self.filter_filename.lower() in entry.name.lower():
            return False
        
        # Select the file
        return True
    
    def __add_to_selection__(self, path):
        """Recursive function that scans the disk and add relevant files to the selection"""
        for entry in path.iterdir():
            
            if self.requirement(entry):
                # Add new member to the selected_files list
                selected_file = Selected_File(self.unique_identifier, self.root_directory, entry)
                self.selected_files.append(selected_file)
                self.unique_identifier+=1
                
            if entry.is_dir():
                # Recursively search subdirectories
                self.__add_to_selection__(entry)

    def copy_report_to_clipboard(self, report_columns):
        # Create a list with only the selected columns in the report
        selected_columns = [text for text, checked in report_columns if checked]

        # Sort in different order, shorter paths first
        self.selected_files.sort( key= lambda selected_file: (len(selected_file.entry.parts), str(selected_file.entry.name.lower() ) ) )

        export = [ '\t'.join(selected_columns) ]

        for selected_file in self.selected_files:    
            export.append('\t'.join([str(selected_file.field(column)) for column in selected_columns]))

        pyperclip.copy('\n'.join(export))
