"""This module defines a dialog box class that reports progress of the search"""

import logging
from PyQt5 import QtCore, QtWidgets
from modules.sf_file_selection import FileSelection
from modules.sf_utilities import app_icon

class SearchProgress(QtWidgets.QDialog):
    """Dialog box that reports progress of the search and closes when the search is complete"""

    def __init__(self, parent=None, search_assignment = None ):
        super().__init__(parent)
        self.setModal(True)

        # Return result
        if search_assignment is None:
            return
        
        # Create window
        self.setWindowTitle("Search for files")
        self.setWindowIcon(app_icon("icon_radar.svg"))
        self.resize(400, 500)

        # Create new worker thread
        self.new_search = FileSelection()
        self.new_search.root_directory = search_assignment.root_directory
        self.new_search.filter_filename = search_assignment.filter_filename
        self.new_search.filter_extension = search_assignment.filter_extension
        self.new_search.filename_case_sensitive = search_assignment.filename_case_sensitive

        # Create a vertical layout with status
        main_layout = QtWidgets.QVBoxLayout()

        main_layout.addWidget(QtWidgets.QLabel(text="Searching for files"))
        main_layout.addWidget(QtWidgets.QLabel(text=f"Directory {self.new_search.root_directory}"))
        if self.new_search.filter_extension:
            main_layout.addWidget(QtWidgets.QLabel(text=f"Extension {self.new_search.filter_extension}"))
        if self.new_search.filter_filename:
            main_layout.addWidget(QtWidgets.QLabel(text=f"Filename containing {self.new_search.filter_filename}"))

        self.progress_label = QtWidgets.QLabel(text="0 files found")
        main_layout.addWidget(self.progress_label)

        # Horizontal layout with buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        self.btn_stop = QtWidgets.QPushButton('Stop searching...', self)
        self.btn_stop.setDefault(True)
        self.btn_stop.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_stop)

        main_layout.addLayout(button_layout)

        # Ceate dummy widget as central widget
        self.setLayout(main_layout)

        # Adjust window size to contents
        self.setFixedWidth(self.sizeHint().width())
        self.setFixedHeight(self.sizeHint().height())

        logging.info("Dialog initialized, creating thread")

        # Create a second thread and tie searching for files to that thread
        self.search_files_thread = QtCore.QThread(parent=self)

        self.new_search.moveToThread(self.search_files_thread)
        self.search_files_thread.started.connect(self.new_search.run)
        self.new_search.finished.connect(self.search_files_thread.quit)
        self.search_files_thread.finished.connect(self.search_files_thread.deleteLater)
        self.new_search.finished.connect(self.thread_is_finished)
        self.new_search.progress.connect(self.report_progress)
        self.search_files_thread.start()

        logging.info("Thread should be started")

    def thread_is_finished(self):
        """Thread has finished searching"""
        logging.info("Search completed")
        file_count = len(self.new_search.selected_files)
        self.progress_label.setText(f"Search completed. {file_count} files found")
        self.progress_label.repaint()
        super().accept()

    def report_progress(self, number_of_files):
        """Thread reports how many files have been found so far"""
        self.progress_label.setText(f"{number_of_files} files found")
        self.progress_label.repaint()

    def result(self):
        """Returning the result from the thread"""
        return self.new_search.selected_files

    def reject(self):
        """Search is interrupted by the user"""
        logging.info("Search is interrupted by the user")

        # Stop the thread
        self.new_search.continue_execution = False
        #self.search_files_thread.exit()

        # Clear the result list
        self.new_search.selected_files = []

        super().reject()
