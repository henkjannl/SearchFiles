"""This script:
- requests a search path
- allows narrowing down search on name or extension
- allows definition of export data
- copies data to clipboard

To do:
- resolve why icons don't work on Lenovo computer
- add 'case sensitive' flag to filename option
- add status bar with relevant info
- search tree:
    - collapse / expand all with right mouse button
- segment window __init__ code in smaller functions
- confirmation message that the files are copied to the clipboard
- first find out if this is a good idea:
    - class Selected_File() can inherit from both QtCore.QObject and
      Path(), instead of creating a self.entry field
    - property decorators for file properties
- add sort field
- reconsider storing the extension field in recently used list
"""

import argparse
import sys
import logging
from pathlib import Path

from PyQt5 import QtGui, QtCore, QtWidgets

from modules.sf_search_progress import SearchProgress
from modules.sf_settings import Settings
from modules.sf_report_columns import SelectReportFields
from modules.sf_utilities import app_icon, app_dir
from modules.sf_file_selection import FileSelection

logging.basicConfig(stream=open(r'.\log.txt', 'w', encoding='utf-8'),
                    level=logging.DEBUG,
                    format='[%(filename)s %(lineno)03d] %(message)s')

# These items sit in a list in the main thread
class FileItem(QtGui.QStandardItem):
    """Item to be displayed in the model view"""

    def __init__(self, selected_file):
        """The item in the first column, giving the name of the file"""
        super().__init__(app_icon("icon_file.ico"), selected_file.entry.name)


class Window(QtWidgets.QMainWindow):
    """Main window"""

    def __init__(self, parent=None, filename_settings = "settings.json"):
        super().__init__(parent)

        logging.info("App dir %s", app_dir("file.txt") )

        self.root_directory = Path().home()

        # Create window
        self.setWindowTitle("Search files on the computer")
        #self.setWindowIcon(app_icon("icon_folder_search.svg"))
        self.setWindowIcon(app_icon("icon_search_folder.ico"))
        
        self.resize(1200, 800)

        # Settings
        self.settings = Settings(filename_settings)
        self.settings.load()

        # Object containing selected files
        self.file_selection = FileSelection()

        # Create a vertical layout with status
        main_layout = QtWidgets.QVBoxLayout()

        font = QtGui.QFont()
        font.setPointSize(10)

        root_dir_box = QtWidgets.QGroupBox("Start directory")
        root_dir_layout = QtWidgets.QHBoxLayout()

        # Button to open file dialog
        # icon_folder = app_icon('icon_folder.svg')
        icon_folder = app_icon('icon_folder.ico')
        root_dir_btn = QtWidgets.QPushButton(icon_folder, '', self)
        root_dir_btn.setIconSize(QtCore.QSize(24,24))
        root_dir_btn.clicked.connect(self.select_root_file)
        root_dir_layout.addWidget(root_dir_btn, stretch=0)

        # Combo box with path
        self.root_dir_combo = QtWidgets.QComboBox(self)
        self.root_dir_combo.setFont(font)
        self.root_dir_combo.addItems(self.settings.recent_directories)
        self.root_dir_combo.setEditable(True)
        self.root_dir_combo.currentIndexChanged.connect(self.root_directory_index_changed)
        self.root_dir_combo.currentTextChanged.connect(self.root_directory_text_changed)

        root_dir_layout.addWidget(self.root_dir_combo, stretch=1)
        root_dir_box.setLayout(root_dir_layout)
        main_layout.addWidget(root_dir_box)

        filter_box = QtWidgets.QGroupBox("Filter files")
        filter_layout = QtWidgets.QGridLayout()

        ext_lbl = QtWidgets.QLabel('File extension')
        #ext_lbl.setFont(font)
        filter_layout.addWidget(ext_lbl, 0, 0)

        self.le_file_extension = QtWidgets.QComboBox(self)
        self.le_file_extension.setFont(font)
        self.le_file_extension.addItems(self.settings.recent_extensions)
        self.le_file_extension.setEditable(True)
        self.le_file_extension.setCurrentText(self.settings.filter_extension)
        self.le_file_extension.currentTextChanged.connect(self.filter_extension_changed)

        filter_layout.addWidget(self.le_file_extension, 0, 1)

        nam_lbl = QtWidgets.QLabel('Filename contains')
        #nam_lbl.setFont(font)
        filter_layout.addWidget(nam_lbl, 0, 2)

        self.le_filename_contains = QtWidgets.QComboBox(self)
        self.le_filename_contains.setFont(font)
        self.le_filename_contains.setEditable(True)
        self.le_filename_contains.addItems(self.settings.recent_filename_filters)
        self.le_filename_contains.setCurrentText(self.settings.filter_filename)
        self.le_filename_contains.currentTextChanged.connect(self.filename_contains_changed)
        filter_layout.addWidget(self.le_filename_contains, 0, 3)

        self.check_case = QtWidgets.QCheckBox("Case sensitive", self)
        self.check_case.setChecked(self.settings.filename_case_sensitive)
        filter_layout.addWidget(self.check_case, 0, 4)

        for col, stch in [(0,0), (1,1), (2,0), (3,3), (4,0)]:
            filter_layout.setColumnStretch(col, stch)
        filter_box.setLayout(filter_layout)
        main_layout.addWidget(filter_box)

        # Execute box
        self.execute_grp = QtWidgets.QGroupBox("Execute search")
        self.execute_lyt = QtWidgets.QHBoxLayout()
        search_btn = QtWidgets.QPushButton(app_icon('icon_search_folder2.ico'),'Search')
        search_btn.clicked.connect(self.search_files)
        self.execute_lyt.addWidget(search_btn)

        self.report_btn = QtWidgets.QPushButton(app_icon('icon_report.ico'),
                                                'Copy report to clipboard')
        self.report_btn.clicked.connect(self.copy_report_to_clipboard)
        self.report_btn.setEnabled(False)
        self.execute_lyt.addWidget(self.report_btn)

        self.execute_lyt.addStretch()
        self.execute_grp.setLayout(self.execute_lyt)
        main_layout.addWidget(self.execute_grp)

        # Create the model and the tree view widget
        self.model = QtGui.QStandardItemModel()
        self.model.setColumnCount(2)
        #self.model.setHorizontalHeaderLabels(['Photo', 'Status'])
        self.directory_tree = {}

        self.tree_view = QtWidgets.QTreeView(self)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setModel(self.model)
        main_layout.addWidget(self.tree_view)

        self.file_items = {}      # Items in the treeview that display filename
        self.comment_items = {}   # Items in the treeview that display status of the file
        self.clear_treeview()

        # Ceate dummy widget as central widget
        widget = QtWidgets.QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

    def select_root_file(self):
        """Event triggered when root file is selected"""
        initial_directory = self.root_dir_combo.currentText()
        self.settings.root_directory = QtWidgets.QFileDialog.getExistingDirectory(self,
            'Select root directory', initial_directory )
        self.root_dir_combo.addItem(self.settings.root_directory)
        self.root_dir_combo.setCurrentIndex (self.root_dir_combo.count()-1)

        self.settings.save()

    def root_directory_index_changed(self):
        """Event triggered when index of root file is changed"""
        self.settings.root_directory = self.root_dir_combo.currentText()
        self.settings.save()

    def root_directory_text_changed(self, new_text):
        """Event triggered when text of the root file is changed"""
        self.settings.root_directory = new_text
        # Do not call settings.save since this will 
        # increase number of recent finds for each character

    def filter_extension_changed(self, new_text):
        """Event triggered when file extension is changed"""
        self.settings.filter_extension = new_text
        self.settings.save()

    def filename_contains_changed(self, new_text):
        """Event triggered when filename contains field is changed"""
        self.settings.filter_filename = new_text
        self.settings.save()

    def search_files(self):
        """Search files and directories"""

        if not Path(self.settings.root_directory).is_dir():
            logging.info('%s not found', self.settings.root_directory)
            return

        self.settings.filename_case_sensitive = self.check_case.isChecked()
        self.settings.save()

        self.file_selection.select_files(self.settings.root_directory,
                                         self.settings.filter_extension,
                                         self.settings.filter_filename,
                                         self.settings.filename_case_sensitive)

        dlg = SearchProgress(self, self.file_selection)
        if dlg.exec()==QtWidgets.QDialog.Accepted:
            self.file_selection.selected_files = list(dlg.result())
        else:
            self.file_selection.new_search()

        self.update_treeview()

        logging.info("End of search_files function")

    def clear_treeview(self):
        """Clear the tree view"""
        logging.info('clear_treeview called')
        self.model.clear()
        self.file_items = {}
        self.model.setColumnCount(1)
        self.model.setHorizontalHeaderLabels(['File'])

        # self.directory_tree is a dictionary of lists
        # Name of the key is directory name
        # The first element of each list is a QtGui.QStandardItem object in the model tree,
        # rooted in self.model.invisibleRootItem()
        # The second element in each list is a recursive dictionary of lists
        self.directory_tree = {}

    def update_treeview(self):
        """Add new items to the tree view"""
        logging.info('update_treeview called')

        self.clear_treeview()

        # Only enable clipboard button if file list is not empty
        self.report_btn.setEnabled( len(self.file_selection.selected_files)>0 )

        # Skip if no files were found
        if len(self.file_selection.selected_files)==0:
            # Todo: perhaps fire a dialog
            return

        # Only create directory entries
        logging.info("Creating directories")
        for selected_file in self.file_selection.selected_files:

            direct_parent = self.model.invisibleRootItem()
            place_in_directory_tree = self.directory_tree

            # Go over path step by step
            for parent in selected_file.parents:

                # Create new dir if needed
                if str(parent) not in place_in_directory_tree.keys():
                    subdirectory = QtGui.QStandardItem(app_icon('icon_folder.ico'), str(parent))
                    font = QtGui.QFont()
                    font.setBold(True)
                    subdirectory.setFont(font)
                    direct_parent.appendRow([subdirectory])
                    place_in_directory_tree[str(parent)] = [subdirectory, {}]

                # Link to new location in the path
                direct_parent, place_in_directory_tree = place_in_directory_tree[str(parent)]

        # Add files to the drectories that were created in the previous step
        logging.info("Adding files to directories")
        for selected_file in self.file_selection.selected_files:

            direct_parent = self.model.invisibleRootItem()
            place_in_directory_tree = self.directory_tree

            # Go over path step by step and lookup the parent of the file to be added
            for parent in selected_file.parents:
                direct_parent, place_in_directory_tree = place_in_directory_tree[str(parent)]

            self.file_items[selected_file.identifier] = FileItem(selected_file)

            direct_parent.appendRow([self.file_items[selected_file.identifier] ])

        self.tree_view.expandAll()
        self.tree_view.header().hide()


    def copy_report_to_clipboard(self):
        """Copy the files found to the clipboard"""
        logging.info('create_report called')
        dlg = SelectReportFields(self, self.settings.report_columns)
        if dlg.exec()==QtWidgets.QDialog.Accepted:
            self.settings.report_columns = dlg.result()
            logging.info(self.settings.report_columns)
            self.file_selection.copy_report_to_clipboard(self.settings.report_columns)
            self.settings.save()

# Main program
if __name__ == '__main__':
    # Parse the arguments to allow the user to use a different settings file on different computers
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", help="Specifies which settings file to use on this computer")
    args = parser.parse_args()

    SETTINGS_FILE = "settings.json"
    if args.settings:
        SETTINGS_FILE = args.settings
        print(f"Using settings file {SETTINGS_FILE}")

    app = QtWidgets.QApplication(sys.argv)
    window = Window(filename_settings = SETTINGS_FILE)
    #stylesheet = """color: white;
    #                background-color: #202020"""
    #window.setStyleSheet(stylesheet)
    window.show()
    sys.exit(app.exec())
