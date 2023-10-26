"""This script:
- requests a search path
- allows narrowing down search on name or extension
- allows definition of export data
- copies data to clipboard

To do:
- allow unique settings file for each client
- search tree:
    - improve sorting directories and files
    - collapse / expand all with right mouse button
- segment window __init__ code in smaller functions
- parallel thread to search files, with dialog that can cancel the search
- first find out if this is a good idea:
    - class Selected_File() can inherit from both QtCore.QObject and Path(), instead of creating a self.entry field
    - property decorators for file properties
- add sort field
"""

import argparse
import sys
import logging
from pathlib import Path
import json
import argparse

from PyQt5 import QtGui, QtCore, QtWidgets

from modules.sf_constants import *
from modules.sf_settings import Settings
from modules.sf_report_columns import *
from modules.sf_utilities import *
from modules.sf_file_selection import *

logging.basicConfig(stream=open(r'.\log.txt', 'w', encoding='utf-8'),
                    level=logging.DEBUG,
                    format='[%(filename)s %(lineno)03d] %(message)s')

# These items sit in a list in the main thread
class File_Item(QtGui.QStandardItem):
    
    def __init__(self, selected_file):
        """The item in the first column, giving the name of the file"""
        super().__init__(app_icon("icon_file.svg"), selected_file.entry.name)

class Comment_Item(QtGui.QStandardItem):

    def __init__(self, selected_file):
        """The item in the second column, representing the status of copying"""
        # Call initializer of QtGui.QStandardItem
        comment = ""
        super().__init__(app_icon("icon_image.svg"), comment)

class DragButton(QtWidgets.QPushButton):

    def __init__(self, label, parent):
        super().__init__(label, parent)

    def mouseMoveEvent(self, e):

        if e.buttons() == QtCore.Qt.LeftButton:
            drag = QtGui.QDrag(self)
            mime = QtCore.QMimeData()
            drag.setMimeData(mime)
            drag.exec_(QtCore.Qt.MoveAction)
            print('drag.exec_')

class Window(QtWidgets.QMainWindow):
    """Main window"""

    def __init__(self, parent=None, settings_file = "settings.json"):
        super().__init__(parent)

        self.root_directory = Path().home()        

        # Create window
        self.setWindowTitle("Search files on the computer")
        self.setWindowIcon(app_icon("icon_folder_search.svg"))
        self.resize(1200, 800)

        # Settings
        self.settings = Settings(settings_file)

        # Object containing selected files
        self.file_selection = File_Selection()
        
        # Create a vertical layout with status
        main_layout = QtWidgets.QVBoxLayout()

        font = QtGui.QFont()
        font.setPointSize(10)

        root_dir_box = QtWidgets.QGroupBox("Start directory")
        root_dir_layout = QtWidgets.QHBoxLayout()

        # Button to open file dialog
        icon_folder = app_icon('icon_folder.svg')
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
        #self.le_file_extension.addItems(['', 'docx', 'xlsx', 'pptx', 'pdf', 'odt', 'odt', 'csv', 'py', 'svg', 'png', 'jpg', 'jpeg', 'gif', 'txt', 'zip'])
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

        for col, stch in [(0,0), (1,1), (2,0), (3,3)]:
            filter_layout.setColumnStretch(col, stch)
        filter_box.setLayout(filter_layout)    
        main_layout.addWidget(filter_box)

        # Execute box
        self.execute_grp = QtWidgets.QGroupBox("Execute search")
        self.execute_lyt = QtWidgets.QHBoxLayout()
        search_btn = QtWidgets.QPushButton(app_icon('icon_folder_search.svg'),'Search')
        search_btn.clicked.connect(self.search_files)
        self.execute_lyt.addWidget(search_btn)

        self.report_btn = QtWidgets.QPushButton(app_icon('icon_report.svg'),'Copy report to clipboard')
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

        # Create thread that looks for the camera
        self.timer = QtCore.QTimer()
        self.timer.setInterval(500)
        #self.timer.timeout.connect(self.scan_for_camera)
        #self.timer.start()

        # Create a second thread and tie searching for files to that thread
        self.move_photos_thread = QtCore.QThread()
        self.file_selection.moveToThread(self.move_photos_thread)

        # Connect signals and slots
        #self.search_for_files_thread.started.connect(self.file_selection.move_copy_files)
        #self.file_selection.finished.connect(self.photo_mover_finished)
        #self.file_selection.status_changed.connect(self.photo_status_changed)

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        pos = e.pos()
        widget = e.source()

        print(f"pos: {pos}")
        print(f"self.column_selection_grp.mapFrom(self, pos): {self.column_selection_grp.mapFrom(self, pos)}")
        print(f"self.unselected_items_grp.geometry(): {self.unselected_items_grp.geometry()}")

        for grp, lbl in [(self.unselected_items_grp, "Unselected items"), 
                         (self.selected_items_grp,   "Selected items"  )  ]:
            if grp.geometry().contains(self.column_selection_grp.mapFrom(self, pos)):
                print(f"Drop target in {lbl}")
            else:
                print(f"Drop target not in {lbl}")

        for grp, lyt in [(self.unselected_items_grp, self.unselected_items_lyt), 
                         (self.selected_items_grp,   self.selected_items_lyt  )  ]:
            local_pos = self.column_selection_grp.mapFrom(self, pos)
            if grp.geometry().contains(local_pos):
                # Drop position is in the group box containing the layout
                target_index = 0
                for n in range(lyt.count()):
                    target_widget = lyt.itemAt(n).widget()

                    if target_widget:
                        if local_pos.x()>target_widget.x()+target_widget.width():
                            print(f"After {n}")
                            target_index = n
                        else:
                            print(f"Before {n}")

                print(f"Target location {target_index}")
                lyt.insertWidget(target_index, widget)
                e.accept()
                return

    def select_root_file(self):
        initial_directory = self.root_dir_combo.currentText()
        self.settings.root_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select root directory', initial_directory )
        self.root_dir_combo.addItem(self.settings.root_directory)
        self.root_dir_combo.setCurrentIndex (self.root_dir_combo.count()-1)

        self.settings.save()

    def root_directory_index_changed(self, index):
        self.settings.root_directory = self.root_dir_combo.currentText()
        self.settings.save()

    def root_directory_text_changed(self, newText):
        self.settings.root_directory = newText
        self.settings.save()

    def filter_extension_changed(self, newText):
        self.settings.filter_extension = newText
        self.settings.save()

    def filename_contains_changed(self, newText):
        self.settings.filter_filename = newText
        self.settings.save()

    def search_files(self):
        """Search files and directories"""
        logging.info(f'get_list_of_photos_from_camera called for {self.settings.root_directory}')
 
        if not Path(self.settings.root_directory).is_dir():
            logging.info(f'{self.settings.root_directory} not found')
            return

        self.file_selection.select_files(self.settings.root_directory, 
                                         self.settings.filter_extension, 
                                         self.settings.filter_filename)

        self.update_treeview()
        
    def clear_treeview(self):
        logging.info('clear_treeview called')
        self.model.clear()
        self.file_items = {}
        self.model.setColumnCount(1)
        self.model.setHorizontalHeaderLabels(['File'])
        

        # self.directory_tree is a dictionary of lists
        # Name of the key is directory name
        # The first element of each list is a QtGui.QStandardItem object in the model tree, rooted in self.model.invisibleRootItem()
        # The second element in each list is a recursive dictionary of lists
        self.directory_tree = {}

    def update_treeview(self):
        """Add new items to the tree view"""
        logging.info('update_treeview called')

        self.clear_treeview()

        # Skip if no files were found
        if len(self.file_selection.selected_files)==0:
            self.report_btn.setEnabled(False)
            #self.result_label.setText("No files were found")
            # Todo: perhaps fire a dialog
            return
        
        for selected_file in self.file_selection.selected_files:

            direct_parent = self.model.invisibleRootItem()
            place_in_directory_tree = self.directory_tree 

            # Go over path step by step
            for parent in selected_file.parents:
                # Create new dir if needed
                if str(parent) not in place_in_directory_tree.keys():
                    subdirectory = QtGui.QStandardItem(app_icon('icon_folder.svg'), str(parent))
                    font = QtGui.QFont()
                    font.setBold(True)
                    subdirectory.setFont(font)
                    direct_parent.appendRow([subdirectory])
                    place_in_directory_tree[str(parent)] = [subdirectory, {}]
                    logging.info(f"Adding directory {str(parent)}")

                # Link to new location in the path
                direct_parent, place_in_directory_tree = place_in_directory_tree[str(parent)]

            self.file_items[selected_file.identifier] = File_Item(selected_file)
            logging.info(f"Adding file {selected_file.entry.name}")

            direct_parent.appendRow([self.file_items[selected_file.identifier] ])

        self.tree_view.expandAll()
        self.tree_view.header().hide()
        #self.tree_view.setColumnWidth(0, 300)

        self.report_btn.setEnabled(True)

        # Skip any further activity if nothing can be done
        #if something_to_do:
            #self.move_photos_action.setEnabled(True)
            #self.copy_photos_action.setEnabled(True)
            #self.set_status(f"{len(self.file_selection.selected_files)} photos found")
        #else:
            #self.set_status("No action required")

    def copy_report_to_clipboard(self):
        logging.info('create_report called')
        dlg = SelectReportFields(self, self.settings.report_columns)
        if dlg.exec()==QtWidgets.QDialog.Accepted:
            self.settings.report_columns = dlg.result()
            logging.info(self.settings.report_columns)
            self.file_selection.copy_report_to_clipboard(self.settings.report_columns)
            self.settings.save()
    
        


##############################
# OLD CODE BELOW
##############################

    def scan_for_camera(self):
        """Scan if the user has connected a camera
        This method is triggered by a timer"""
        camera_connected = False
        for potential_camera_location in self.settings[SETTING_LIST_OF_CAMERA_LOCATIONS]:
            if Path(potential_camera_location).is_dir():
                camera_connected = True
                if self.state == STATE_SCANNING:
                    logging.info(f'Found camera at {potential_camera_location}')
                    self.locate_camera_action.setChecked(False)
                    self.set_origin(potential_camera_location)
                    self.list_origin = LIST_ORIGIN_CAMERA
                    self.search_files()
                    self.state = STATE_AUTO_LIST_RETRIEVED
                break

        self.set_camera_connected_icon(camera_connected, self.list_origin==LIST_ORIGIN_CAMERA)

    def locate_camera(self):
        """User requests to open a directory which contains photos"""
        logging.info('locate_camera called')
        camera_dir = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select camera', self.most_likely_camera_location() )

        if Path(camera_dir).is_dir():
            camera_dir = str(Path(camera_dir))
            self.toggle_scanning_action.setChecked(False)
            self.settings[SETTING_LAST_MANUAL_CAMERA_LOCATION] = camera_dir
            self.set_origin(camera_dir)
            self.save_settings()
            self.list_origin = LIST_ORIGIN_MANUAL
            self.search_files()
            self.state = STATE_MANUAL_LIST_RETRIEVED

    def photo_status_changed(self, identifier, new_status):
        """The mover thread has modified the status of a file"""
        logging.info(f'Status of {identifier:03d} changed to {FILE_STATUS_STRING[new_status]}')
        if identifier in self.comment_items:
            self.comment_items[identifier].update_status(new_status)

    def choose_destination_directory(self):
        """User changes destination directory"""
        logging.info('choose_destination_directory called')
        new_target_location = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select target location', self.most_likely_target_location() )
        self.set_target(new_target_location)
        self.save_settings()
        self.update_treeview()

    def move_photos(self):
        logging.info('move_photos called')
        self.file_selection.set_target_location(self.settings[SETTING_CURRENT_TARGET_LOCATION])
        self.file_selection.only_copy = False
        self.move_photos_action.setEnabled(False)
        self.copy_photos_action.setEnabled(False)
        self.state = STATE_MOVE_COPY_PHOTOS
        self.move_photos_thread.start()

    def copy_photos(self):
        logging.info('copy_photos called')
        self.file_selection.set_target_location(self.settings[SETTING_CURRENT_TARGET_LOCATION])
        self.file_selection.only_copy = True
        self.move_photos_action.setEnabled(False)
        self.copy_photos_action.setEnabled(False)
        self.state = STATE_MOVE_COPY_PHOTOS
        self.move_photos_thread.start()

    def photo_mover_finished(self, message):
        logging.info('photo_mover_finished called')
        #self.photo_mover.stop()
        self.move_photos_thread.quit()
        self.move_photos_thread.wait()

        # Update list and enable/disable buttons
        self.update_treeview()
        self.set_status(message)

        self.move_photos_action.setEnabled(True)
        self.copy_photos_action.setEnabled(True)

        self.state = STATE_SCANNING

    def load_settings(self):
        logging.info('load_settings called')
        logging.info(f'Settings file: {SETTINGS_FILE}')
        try:
            with open(SETTINGS_FILE, 'r') as openfile:        
                self.settings = json.load(openfile)
        except:
            self.settings = {}
            self.settings[SETTING_LIST_OF_CAMERA_LOCATIONS] = [r'D:\AVF_INFO', r'D:\DCIM', r'D:\PRIVATE', r'E:\AVF_INFO', r'E:\DCIM', r'E:\PRIVATE']
            self.settings[SETTING_CURRENT_CAMERA_LOCATION    ] = r'C:\Users\henkj\Downloads\Source'
            self.settings[SETTING_LIST_OF_TARGET_LOCATIONS] = [r'C:\Users\OneDrive\Fotos', r'C:\Users\hjvanderpol\OneDrive\Fotos', 
                r'C:\Users\hj.vanderpol', r'C:\Source']
            self.settings[SETTING_CURRENT_TARGET_LOCATION] = Path.home()

    def clean_path_list(self, path_list):
        new_list = []
        for path in path_list:
            modified_path = str(Path(path))
            if modified_path not in new_list:
                new_list.append(modified_path)
        return new_list

    def cleanup_settings(self):
        logging.info('cleanup_settings called')

        if SETTING_VERSION not in self.settings.keys():
            self.settings[SETTING_VERSION] = 1

        if SETTING_LIST_OF_CAMERA_LOCATIONS not in self.settings.keys():
            self.settings[SETTING_LIST_OF_CAMERA_LOCATIONS] = []
        self.settings[SETTING_LIST_OF_CAMERA_LOCATIONS] = self.clean_path_list(self.settings[SETTING_LIST_OF_CAMERA_LOCATIONS])

        if SETTING_CURRENT_CAMERA_LOCATION not in self.settings.keys():
            self.settings[SETTING_CURRENT_CAMERA_LOCATION] = str(Path.home())
        self.settings[SETTING_CURRENT_CAMERA_LOCATION] = str(Path(self.settings[SETTING_CURRENT_CAMERA_LOCATION]))

        if SETTING_LAST_MANUAL_CAMERA_LOCATION not in self.settings.keys():
            self.settings[SETTING_LAST_MANUAL_CAMERA_LOCATION] = str(Path.home())

        if SETTING_LIST_OF_TARGET_LOCATIONS not in self.settings.keys():
            self.settings[SETTING_LIST_OF_TARGET_LOCATIONS] = []
        self.settings[SETTING_LIST_OF_TARGET_LOCATIONS] = self.clean_path_list(self.settings[SETTING_LIST_OF_TARGET_LOCATIONS])

        if SETTING_CURRENT_TARGET_LOCATION not in self.settings.keys():
            self.settings[SETTING_CURRENT_TARGET_LOCATION] = str(Path.home())
        self.settings[SETTING_CURRENT_TARGET_LOCATION] = str(Path(self.settings[SETTING_CURRENT_TARGET_LOCATION]))

    def save_settings(self):
        logging.info('save_settings called')
        self.cleanup_settings()
        json_settings_object = json.dumps(self.settings, indent=4)
        with open(SETTINGS_FILE, "w") as outfile:
            outfile.write(json_settings_object)

    def most_likely_camera_location(self):

        # If the last used camera position exists, return that
        if Path(self.settings[SETTING_LAST_MANUAL_CAMERA_LOCATION]).is_dir():
            return self.settings[SETTING_LAST_MANUAL_CAMERA_LOCATION]
        
        # If one of the previously used camera positions works, return that
        for potential_camera_location in self.settings[SETTING_LIST_OF_CAMERA_LOCATIONS]:
            if Path(potential_camera_location).is_dir():
                return potential_camera_location

        # Finally return the user directory
        return self.settings[SETTING_LAST_MANUAL_CAMERA_LOCATION]

    def most_likely_target_location(self):
        # If the last used target location exists, return that
        if Path(self.settings[SETTING_CURRENT_TARGET_LOCATION]).is_dir():
            return self.settings[SETTING_CURRENT_TARGET_LOCATION]
        
        # If one of the previously used target locations works, return that
        for potential_target_location in self.settings[SETTING_LIST_OF_TARGET_LOCATIONS]:
            if Path(potential_target_location).is_dir():
                return potential_target_location

        # Finally return the user directory
        return str(Path.home())

if __name__ == '__main__':
    # Parse the arguments to allow the user to use a different settings file on different computers
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", help="Specifies which settings file to use on this computer")
    args = parser.parse_args()

    settings_file = "settings.json"
    if args.settings:
        settings_file = args.settings
        print(f"Using settings file {settings_file}")

    app = QtWidgets.QApplication(sys.argv)
    window = Window(settings_file = settings_file)
    #stylesheet = """color: white;
    #                background-color: #202020"""
    #window.setStyleSheet(stylesheet)
    window.show()
    sys.exit(app.exec())
