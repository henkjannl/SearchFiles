"""This module defines a dialog box class that allows the user to define columns to
be included in the report, and drag them in the right order"""

import logging
from PyQt5 import QtCore, QtWidgets
import modules.sf_constants as const
from modules.sf_utilities import app_icon

class SelectReportFields(QtWidgets.QDialog):
    """Dialog box that allows the user to define columns to
    be included in the report, and drag them in the right order"""

    def __init__(self, parent=None, list_of_columns = None ):
        super().__init__(parent)
        self.setModal(True)

        # Return result
        if list_of_columns is None:
            self.list_of_columns = const.DEFAULT_COLUMNS
        else:
            self.list_of_columns = list_of_columns

        # Create window
        self.setWindowTitle("Select columns")
        self.setWindowIcon(app_icon("icon_copied.svg"))
        self.resize(400, 500)

        # Create a vertical layout with status
        main_layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel(text="Select columns to display."
                                 "Drag the columns to modify the order")
        main_layout.addWidget(label)

        # List of selectable fields
        self.fields_list = QtWidgets.QListWidget()

        for text, checked in list_of_columns:
            item = QtWidgets.QListWidgetItem(text)
            item.setCheckState({False: QtCore.Qt.Unchecked, True: QtCore.Qt.Checked}[checked])
            self.fields_list.addItem(item)
        self.fields_list.setDragDropMode(self.fields_list.InternalMove)

        main_layout.addWidget(self.fields_list)

        # Horizontal layout with buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        self.btn_confirm = QtWidgets.QPushButton('OK', self)
        self.btn_confirm.setDefault(True)
        self.btn_confirm.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_confirm)
        self.btn_cancel = QtWidgets.QPushButton('Cancel', self)
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(button_layout)

        # Ceate dummy widget as central widget
        self.setLayout(main_layout)

    def result(self):
        """Returning the columns from the dialog"""
        # Depending on calling the accept member, the original list or the modified list is returned
        return self.list_of_columns

    def accept(self):
        """Triggered when the user clicks OK"""
        # Overwrite the initial list of selected and unselected items
        logging.info("Accepted")
        self.list_of_columns =  [ [self.fields_list.item(row).text(), self.fields_list.item(row).checkState() == QtCore.Qt.Checked] 
                                 for row in range(self.fields_list.count())]
        logging.info(self.list_of_columns)
        super().accept()
