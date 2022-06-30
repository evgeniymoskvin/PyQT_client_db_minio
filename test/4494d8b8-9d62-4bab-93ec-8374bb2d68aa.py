from PySide2 import QtCore, QtWidgets
import requests

from ui.clientdb import Ui_Form


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_list = []
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setAcceptDrops(True)
        self.ui.pd_open_file.clicked.connect(self.showDialog)
        self.ui.pd_send_file.clicked.connect(self.post_file)

    def dragEnterEvent(self, event):
        # Тут выполняются проверки и дается (или нет) разрешение на Drop
        mime = event.mimeData()

        # Если перемещаются ссылки
        if mime.hasUrls():
            # Разрешаем действие перетаскивания
            event.acceptProposedAction()

    def dropEvent(self, event):
        # Обработка события Drop

        for url in event.mimeData().urls():
            file_name = url.toLocalFile()
            print(file_name)
            self.file_list.append(url.toLocalFile())
            self.ui.listWidget.addItem(file_name)

        # self.updateLabels()

        return super().dropEvent(event)

    def showDialog(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file')[0]
        print(fname)
        self.file_list.append(fname)
        self.ui.listWidget.addItem(f'{fname}')
        # for url in event.mimeData().urls():
        #     file_name = url.toLocalFile()

    def post_file(self):
        files = []
        for file_local in self.file_list:
            print(file_local)
            files.append(('files', open(f'{file_local}', 'rb')))
        url = 'http://127.0.0.1:8000/frames'
        resp = requests.post(url=url, files=files)
        print(resp.json())


if __name__ == '__main__':
    app = QtWidgets.QApplication()

    win = MainWindow()
    win.show()

    app.exec_()
