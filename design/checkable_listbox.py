import sys

from PyQt5.QtWidgets import QApplication, QListWidget, QListWidgetItem, QComboBox
from PyQt5.QtCore import Qt

if __name__ == '__main__':
    app = QApplication(sys.argv)

    lw = QListWidget()
    #lw = QComboBox()
    for i in range(5):
        text = { 0: 'Path', 1: 'Filename', 2: 'Filesize', 3: 'Path+Filename', 4: 'CreateDate'}[i]
        item = QListWidgetItem(text)
        item.setCheckState(Qt.Unchecked)
        lw.addItem(item)
    lw.setDragDropMode(lw.InternalMove)
    lw.show()
    sys.exit(app.exec_())