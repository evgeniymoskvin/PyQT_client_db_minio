from PySide2 import QtCore, QtWidgets, QtGui
import requests
from ui.clientdb import Ui_Form
from minio import Minio

client = Minio(
    "194.87.99.84:9000",
    access_key="DJxkijWpi9zI9Qm5",
    secret_key="SfIpv9R98IOBM87ETYuPcATe59BByp7K",
    secure=False
)


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_list = []  # список файлов для отправки
        self.download_list_files = []  # список файлов для загрузки
        self.url = 'http://127.0.0.1:8000'
        self.bucket_name = None  # Название корзины min.io для загрузки файла
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setAcceptDrops(True)
        self.ui.pb_download_all.setEnabled(False)
        self.ui.pb_delete.setEnabled(False)
        self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self)
        self.shortcut.activated.connect(self.showOpenDialog)
        self.ui.pd_open_file.clicked.connect(self.showOpenDialog)
        self.ui.pd_send_file.clicked.connect(self.post_file)
        self.ui.pb_get_info.clicked.connect(self.get_info)
        self.ui.pb_download_all.clicked.connect(self.showSaveDialog)
        self.ui.pb_delete.clicked.connect(self.delete_files)

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
            self.file_list.append(url.toLocalFile())
            self.ui.listWidget.addItem(file_name)

        return super().dropEvent(event)

    def showOpenDialog(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file')[0]
        print(fname)
        self.file_list.append(fname)
        self.ui.listWidget.addItem(f'{fname}')

    def post_file(self):
        files = []
        for file_local in self.file_list:
            print(file_local)
            files.append(('files', open(f'{file_local}', 'rb')))
        resp = requests.post(url=f'{self.url}/frames/', files=files)
        print(resp.json())
        QtWidgets.QMessageBox.warning(self, "Готово", f"Файлы отправлены. Ваш номер запроса: {resp.json()['request_number']}")

    def get_info(self):
        source = self.ui.getinfoline.text()
        resp = requests.get(f"{self.url}/frames/{source}")
        if 'error' not in resp.json().keys():
            self.ui.pb_download_all.setEnabled(True)
            self.ui.pb_delete.setEnabled(True)
            dict_ = resp.json()
            for key in dict_:
                if key != "request_number":
                    temp_list = [val for val in dict_[key].values()]
                    temp_list.append("Скачать")
                    self.download_list_files.append(temp_list)
            print(self.download_list_files)
            self.model = TableModel(self.download_list_files)
            # self.model.setHeaderData(0, QtCore.Qt.Horizontal, "№")
            self.model.setHeaderData(0, QtCore.Qt.Horizontal, "Название файла")
            self.model.setHeaderData(1, QtCore.Qt.Horizontal, "Дата регистрации")
            self.ui.tableView.setModel(self.model)
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Неправильный номер запроса")

    def delete_files(self):
        source = self.ui.getinfoline.text()
        reply = QtWidgets.QMessageBox.question(self, 'Удалить файлы?',
                                               f'Удалить запрос {source} и его файлы из хранилища?',
                                               QtWidgets.QMessageBox.Yes,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            requests.delete(f"{self.url}/frames/{source}")

    def showSaveDialog(self):
        fname = QtWidgets.QFileDialog.getExistingDirectoryUrl(self, "Save as").url()[8:]
        self.bucket_name = self.ui.getinfoline.text()
        try:
            source = self.ui.getinfoline.text()
            resp = requests.get(f"{self.url}/bucket/{source}")
            for item in self.download_list_files:
                client.fget_object(resp.json()['bucket_name'], item[0], f"{fname}/{item[0]}")
            # print(resp.json()['bucket_name'])
        except:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Ошибка загрузки")
        # print(fname.url())

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        reply = QtWidgets.QMessageBox.question(self, 'Закрыть окно?', 'Вы хотите закрыть окно?',
                                               QtWidgets.QMessageBox.Yes,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])


if __name__ == '__main__':
    app = QtWidgets.QApplication()

    win = MainWindow()
    win.show()

    app.exec_()
