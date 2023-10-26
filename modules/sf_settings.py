import logging
from pathlib import Path
import json

from modules.sf_constants import *
from modules.sf_utilities import *

class Settings():
    def __init__(self, settings_file = "settings.json"):
        self.settings_file = app_dir(settings_file)

        self.settings_version = 1 # Allows for backward compatibility in the future
        self.root_directory = str(Path(Path().home(), 'Downloads'))
        self.recent_directories = []
        self.filter_extension = ''
        self.recent_extensions = ['', 'docx', 'xlsx', 'pptx', 'pdf', 'odt', 'odt', 'csv', 
                                  'py', 'svg', 'png', 'jpg', 'jpeg', 'gif', 'txt', 'zip']
        self.filter_filename = ''
        self.recent_filename_filters = []

        # Name of the column, followed by a boolean which tells whether it is shown
        self.report_columns = [(COL_PATH,             True  ), 
                               (COL_FILE_NAME,        True  ), 
                               (COL_FILE_SIZE,        False ), 
                               (COL_PATH_AND_NAME,    False ), 
                               (COL_CREATE_DATE,      False ),
                               (COL_MODIFIED_DATE,    False ),
                               (COL_ACCESSED_DATE,    False ),
                               (COL_IMAGE_TAKEN_DATE, False ),
                               (COL_IMAGE_WIDTH,      False ),
                               (COL_IMAGE_HEIGHT,     False )  ]

        # Overrule default values with values from disk
        self.load()

    def cleanup(self):
        """Maintains recent lists and cleans up settings data"""
        # Maintain the list of recent directories
        self.root_directory = str(Path(self.root_directory))
        self.recent_directories = [ str(Path(directory_name)) for directory_name in self.recent_directories]
        if self.root_directory not in self.recent_directories:
            self.recent_directories.insert(0, self.root_directory)

        if len(self.recent_directories)>10:
            self.recent_directories = self.recent_directories[:10]

        # Maintain the list of recent extensions
        if self.filter_extension not in self.recent_extensions:
            self.recent_extensions.insert(0, self.filter_extension)

        # Do not limit the recent extension list

        # Maintain the list of recent filenames
        if self.filter_filename not in self.recent_filename_filters:
            self.recent_filename_filters.insert(0, self.filter_filename)

        if len(self.recent_filename_filters)>10:
            self.recent_filename_filters = self.recent_filename_filters[:10]

    def load(self):
        logging.info(f'load_settings called for {str(self.settings_file)}')
        settings_dict = {}
        if self.settings_file.exists() and not self.settings_file.is_dir():
            with open(self.settings_file, 'r') as openfile:        
                settings_dict = json.load(openfile)

        if SETTINGS_VERSION in settings_dict.keys():
            self.settings_version        = settings_dict[SETTINGS_VERSION]

        if SETTINGS_ROOT_DIRECTORY in settings_dict.keys():
            self.root_directory          = settings_dict[SETTINGS_ROOT_DIRECTORY]

        if SETTINGS_RECENT_DIRECTORIES in settings_dict.keys():
            self.recent_directories      = settings_dict[SETTINGS_RECENT_DIRECTORIES]

        if SETTINGS_FILTER_EXTENSION in settings_dict.keys():
            self.filter_extension        = settings_dict[SETTINGS_FILTER_EXTENSION]

        if SETTINGS_RECENT_EXTENSIONS in settings_dict.keys():
            self.recent_extensions       = settings_dict[SETTINGS_RECENT_EXTENSIONS]

        if SETTINGS_FILTER_FILENAME in settings_dict.keys():
            self.filter_filename         = settings_dict[SETTINGS_FILTER_FILENAME]

        if SETTINGS_RECENT_FILENAMES in settings_dict.keys():
            self.recent_filename_filters = settings_dict[SETTINGS_RECENT_FILENAMES]

        if SETTINGS_REPORT_COLUMNS in settings_dict.keys():
            self.report_columns = settings_dict[SETTINGS_REPORT_COLUMNS]


    def save(self):
        logging.info(f'save_settings called for {self.settings_file}')

        self.cleanup()

        settings_dict = {}
        settings_dict[SETTINGS_VERSION]            = self.settings_version
        settings_dict[SETTINGS_ROOT_DIRECTORY]     = self.root_directory
        settings_dict[SETTINGS_RECENT_DIRECTORIES] = self.recent_directories
        settings_dict[SETTINGS_FILTER_EXTENSION]   = self.filter_extension
        settings_dict[SETTINGS_RECENT_EXTENSIONS]  = self.recent_extensions
        settings_dict[SETTINGS_FILTER_FILENAME]    = self.filter_filename
        settings_dict[SETTINGS_RECENT_FILENAMES]   = self.recent_filename_filters
        settings_dict[SETTINGS_REPORT_COLUMNS]     = self.report_columns

        json_settings_object = json.dumps(settings_dict, indent=4)
        with open(self.settings_file, "w") as outfile:
            outfile.write(json_settings_object)

