"""sf_file_selection defines:
- a class Selected_File containing files, which can be shown in a PyQt5 treeview
- a class File_Selection that holds the list of selected files
"""

import logging
from datetime import datetime
from pathlib import Path
from PyQt5 import QtCore
import pyperclip

import modules.sf_constants as const
from modules.sf_utilities import image_size, image_taken_date

# This object sits in the parallel thread that moves files from camera to computer
class SelectedFile(QtCore.QObject):
    """File to be shown in a PyQt tree view"""

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

    def extension(self):
        """File extension"""
        return Path(self.entry).suffix[1:]
    
    def file_size(self):
        """File size of the file"""
        return self.entry.stat().st_size

    def created(self):
        """The date and time the file was created, formatted as string"""
        return datetime.fromtimestamp(self.entry.stat().st_ctime).strftime(const.DATE_FMT)

    def modified(self):
        """The date and time the file was modified, formatted as string"""
        return datetime.fromtimestamp(self.entry.stat().st_mtime).strftime(const.DATE_FMT)

    def accessed(self):
        """The date and time the file was last accessed, formatted as string"""
        return datetime.fromtimestamp(self.entry.stat().st_atime).strftime(const.DATE_FMT)

    def directory(self):
        """Directory in which the file resides"""
        return str(self.entry.parent)

    def full_path(self):
        """The full path of the file"""
        return str(self.entry.resolve() )

    def image_width(self):
        """The width of the image, if the file is an image, or an empty string if it is not"""
        if self.image_size is None:
            self.image_size = image_size(self.entry)

        return self.image_size[0]

    def image_height(self):
        """The height of the image, if the file is an image, or an empty string if it is not"""
        if self.image_size is None:
            self.image_size = image_size(self.entry)

        return self.image_size[0]

    def field(self, field):
        """Returns the field, if the field is specified as a string"""
        #ToDo: redefine as a directory
        if field==const.COL_PATH:
            return self.directory()
        elif field==const.COL_FILE_NAME:
            return self.entry.name
        elif field==const.COL_FILE_EXTENSION:
            return self.extension()
        elif field==const.COL_FILE_SIZE:
            return self.file_size()
        elif field==const.COL_PATH_AND_NAME:
            return self.full_path()
        elif field==const.COL_CREATE_DATE:
            return self.created()
        elif field==const.COL_MODIFIED_DATE:
            return self.modified()
        elif field==const.COL_ACCESSED_DATE:
            return self.accessed()
        elif field==const.COL_IMAGE_TAKEN_DATE:
            return image_taken_date(self.entry)
        elif field==const.COL_IMAGE_WIDTH:
            return self.image_width()
        elif field==const.COL_IMAGE_HEIGHT:
            return self.image_height()
        else:
            return "Invalid field"

class FileSelection(QtCore.QObject):
    """Creates list of files as a result of the search
       By subclassing the list from QObject, 
       the search can be moved to a separate thread"""
    
    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal(int)

    def __init__(self):
        """Initialize the the file selection list object
        The unique identifier is needed to link a file in the GUI to a file in the list.
        If a file in the list is directly displayed in the GUI, a multithreading problem occurs"""
        super().__init__(None)
        self.root_directory = ''
        self.filter_extension = ''
        self.filter_filename = ''
        self.unique_identifier = 0
        self.selected_files = []
        self.continue_execution = True

    def new_search(self):
        self.unique_identifier = 0
        self.selected_files = []
        self.continue_execution = True

    def select_files(self, root_directory, filter_extension, filter_filename):
        """Set search variables"""
        self.root_directory = Path(root_directory)
        self.filter_extension = filter_extension
        self.filter_filename = filter_filename
        self.new_search()

    def run(self):
        """Start search progress in separate thread"""
        logging.info("Starting search")
        self.new_search()
        self.__add_to_selection__( Path(self.root_directory) )

        # Sort files, directories first, then sort on filename
        self.selected_files.sort( key= lambda selected_file:
            (selected_file.entry.is_dir(), str(selected_file.full_path() ) ) )

        logging.info("%d files found", len(self.selected_files) )
        self.finished.emit()

    def requirement(self, entry):
        """Filter the files that were found
        Override this member to make a different selection"""

        # Do not select directories
        if entry.is_dir():
            return False

        # Do not select if extension requirement is not met
        # ToDo: compare actual extension, instead of endswith
        # ToDo: ensure filter '' is still selecting all files
        if self.filter_extension and Path(entry).suffix[1:] != self.filter_extension:
            #logging.info("Search declined since [%s] is not [%s]", )
            return False

        # Do not select if filename filter requirement is not met
        if not self.filter_filename.lower() in entry.name.lower():
            return False

        # Select the file
        return True

    def __add_to_selection__(self, path):
        """Recursive function that scans the disk and add relevant files to the selection"""        
        for entry in path.iterdir():

            # Allow the user to interrupt the search
            if not self.continue_execution:
                return

            if self.requirement(entry):
                # Add new member to the selected_files list
                selected_file = SelectedFile(self.unique_identifier, self.root_directory, entry)
                self.selected_files.append(selected_file)
                self.unique_identifier+=1
                if self.unique_identifier % 100 == 0:
                    self.progress.emit( len(self.selected_files) )

            if entry.is_dir():
                # Recursively search subdirectories
                self.__add_to_selection__(entry)

    def copy_report_to_clipboard(self, report_columns):
        """Create a list with only the selected columns in the report"""
        logging.info('copy_report_to_clipboard:')
        logging.info(report_columns)
        selected_columns = [text for text, checked in report_columns if checked]

        # Sort in different order, shorter paths first
        self.selected_files.sort( key= lambda selected_file:
                        (len(selected_file.entry.parts), str(selected_file.entry.name.lower() ) ) )

        export = [ '\t'.join(selected_columns) ]

        for selected_file in self.selected_files:
            export.append('\t'.join([str(selected_file.field(column)) \
                                     for column in selected_columns]))

        pyperclip.copy('\n'.join(export))
