import sys

from PyQt5 import QtGui, QtCore, QtWidgets
from modules.sf_utilities import *

class SelectReportFields(QtWidgets.QDialog):
    def __init__(self, parent=None, list_of_columns = [('Path', True), ('Filename', True), ('Filesize', False), ('Path+Filename', False), ('CreateDate', False)]):
        super().__init__(parent)
        self.setModal(True)

        # Return result
        self.list_of_columns = list_of_columns

        # Create window
        self.setWindowTitle("Select columns")
        self.setWindowIcon(app_icon("icon_copied.svg"))
        self.resize(400, 500)

        # Create a vertical layout with status
        main_layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel(text="Select columns to display. Drag the columns to modify the order")
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
        self.btn_OK = QtWidgets.QPushButton('OK', self)
        self.btn_OK.setDefault(True)
        self.btn_OK.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_OK)
        self.btn_Cancel = QtWidgets.QPushButton('Cancel', self)
        self.btn_Cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_Cancel)

        main_layout.addLayout(button_layout)

        # Ceate dummy widget as central widget
        self.setLayout(main_layout)

    def result(self):
        # Depending on calling the accept member, the original list or the modified list is returned
        return self.list_of_columns
    
    def accept(self):
        # Overwrite the initial list of selected and unselected items
        logging.info("Accepted")
        self.list_of_columns = [ ( self.fields_list.item(row).text(), (self.fields_list.item(row).checkState() == QtCore.Qt.Checked) ) for row in range(self.fields_list.count()) ]
        super().accept()
