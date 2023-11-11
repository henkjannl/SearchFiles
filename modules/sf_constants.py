"""Constants used in various places"""

# Constants
# Keywords in the settings file (json)
SETTINGS_VERSION                 = "Version"
SETTINGS_ROOT_DIRECTORY          = "RootDir"
SETTINGS_RECENT_DIRECTORIES      = "RecentDirectories"
SETTINGS_FILTER_EXTENSION        = "FilterExtension"
SETTINGS_RECENT_EXTENSIONS       = "RecentExtensions"
SETTINGS_FILTER_FILENAME         = "FilterFilename"
SETTINGS_FILENAME_CASE_SENSITIVE = "FilenameCaseSensitive"
SETTINGS_RECENT_FILENAMES        = "RecentFilenames"
SETTINGS_REPORT_COLUMNS          = "ReportColumns"

# Column names in the report
COL_PATH              = 'Path'
COL_FILE_NAME         = 'Filename'
COL_FILE_EXTENSION    = 'Extension'
COL_FILE_SIZE         = 'File size'
COL_PATH_AND_NAME     = 'Path and filename'
COL_PATH_DEPTH        = 'Path depth'
COL_CREATE_DATE       = 'Create date'
COL_MODIFIED_DATE     = 'Modified date'
COL_ACCESSED_DATE     = 'Accessed date'
COL_IMAGE_TAKEN_DATE  = 'Image taken date'
COL_IMAGE_WIDTH       = 'Image width'
COL_IMAGE_HEIGHT      = 'Image height'

# Default columns
DEFAULT_COLUMNS = [
    (COL_PATH              , True   ),
    (COL_FILE_NAME         , True   ),
    (COL_FILE_SIZE         , True   ),
    (COL_FILE_EXTENSION    , True   ),
    (COL_PATH_DEPTH        , False  ),
    (COL_CREATE_DATE       , False  ),
    (COL_MODIFIED_DATE     , False  ),
    (COL_ACCESSED_DATE     , False  ),
    (COL_IMAGE_TAKEN_DATE  , False  ),
    (COL_IMAGE_WIDTH       , False  ),
    (COL_IMAGE_HEIGHT      , False  ),
    (COL_PATH_AND_NAME     , False  ) ]

# Date format used for files
DATE_FMT = '%Y-%m-%d %H:%M:%S'
