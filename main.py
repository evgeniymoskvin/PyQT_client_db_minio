import sys

import requests
from PySide2 import QtCore, QtWidgets, QtGui
from ui.clientdb import Ui_Form
from settings import client


class PushButtonDelegate(QtWidgets.QStyledItemDelegate):
    clicked = QtCore.Signal(QtCore.QModelIndex)

    def paint(self, painter, option, index):
        if (isinstance(self.parent(), QtWidgets.QAbstractItemView)
                and self.parent().model() is index.model()):

            self.parent().openPersistentEditor(index)


    def createEditor(self, parent, option, index):
        button = QtWidgets.QPushButton(parent)
        button.clicked.connect(lambda *args, ix=index: self.clicked.emit(ix))
        return button

    def setEditorData(self, editor, index):
        editor.setText("Скачать")

    def setModelData(self, editor:QtWidgets.QWidget, model:QtCore.QAbstractItemModel, index:QtCore.QModelIndex) -> None:
        pass

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_list = []  # список файлов для отправки
        self.download_list_files = []  # список файлов для загрузки
        self.url = 'http://127.0.0.1:8000'
        self.bucket_name = None  # Название корзины min.io для загрузки файла

        self.ui = Ui_Form()  # инициализируем окно
        self.init_about_window()  # инициализируем окно about
        self.ui.setupUi(self)

        self.initStatusConnection()  # Проверяем статус подключения при загрузке программы

        self.ui.pb_reconnect.clicked.connect(self.initStatusConnection)  # Кнопка reconnect

        self.ui.pb_download_all.setEnabled(False)
        self.ui.pb_delete.setEnabled(False)

        self.ui.pd_open_file.clicked.connect(self.add_files_to_send)
        self.ui.pd_send_file.setEnabled(False)
        self.ui.pd_send_file.clicked.connect(self.post_file)
        self.ui.pb_get_info.clicked.connect(self.get_info)
        self.ui.pb_download_all.clicked.connect(self.save_all_files)
        self.ui.pb_delete.clicked.connect(self.delete_files)
        self.ui.pb_about.clicked.connect(self.open_about)
        self.openDelegate = PushButtonDelegate()
        self.openDelegate.clicked.connect(self.download_file)

    def initStatusConnection(self):
        """
        Проверяем подключение к серверу.
        :return:
        """
        try:
            resp = requests.get(self.url)
            if resp.status_code == 200:
                self.ui.statusLabel.setText("Подключено")
                self.ui.getinfoline.setEnabled(True)
                self.ui.pb_get_info.setEnabled(True)
                self.ui.listWidget.setEnabled(True)
                self.setAcceptDrops(True)  # Подключаем Drag and Drop
                self.ui.pd_open_file.setEnabled(True)  # Делаем активной кнопку выбора файлов
                # Подключаем горячие клавиши
                self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+O"), self)
                self.shortcut.activated.connect(self.add_files_to_send)
        except requests.exceptions.ConnectionError:
            self.ui.statusLabel.setText("Подключение отсутствует")
            self.ui.getinfoline.setEnabled(False)
            self.ui.pb_get_info.setEnabled(False)
            self.ui.listWidget.setEnabled(False)
            self.setAcceptDrops(False)
            self.ui.pd_open_file.setEnabled(False)

    def init_about_window(self):
        self.child_window = AboutWindow()

    def open_about(self):
        self.child_window.show()

    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_name = url.toLocalFile()
            self.file_list.append(url.toLocalFile())
            self.ui.listWidget.addItem(file_name)

        self.ui.pd_send_file.setEnabled(True)
        return super().dropEvent(event)

    def add_files_to_send(self):
        """
        Функция добавления файлов на отправку.
        """
        # Через диалоговое окно OpenFile получаем ссылку на файла
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file')[0]
        print(fname)
        self.file_list.append(fname)
        self.ui.listWidget.addItem(f'{fname}')
        self.ui.pd_send_file.setEnabled(True)

    def post_file(self):
        """
        Отправка файлов на сервис по api
        """
        files = []
        for file_local in self.file_list:
            print(file_local)
            files.append(('files', open(f'{file_local}', 'rb')))
        resp = requests.post(url=f'{self.url}/frames/', files=files)
        QtWidgets.QMessageBox.information(self, "Готово",
                                          f"Файлы отправлены. Ваш номер запроса: {resp.json()['request_number']}")

    def get_info(self):
        """
        Получаем информацию об отправке
        """
        source = self.ui.getinfoline.text()  # Получаем номер отправки из lineEdit
        self.download_list_files.clear()
        resp = requests.get(f"{self.url}/frames/{source}")
        if 'error' not in resp.json().keys():
            self.ui.pb_download_all.setEnabled(True)
            self.ui.pb_delete.setEnabled(True)
            dict_ = resp.json()
            headers = ["№", "Название", "Дата регистрации", "Загрузить"]
            stm = QtGui.QStandardItemModel()
            stm.setHorizontalHeaderLabels(headers)
            for key in dict_:
                if key != "request_number":
                    try:
                        temp_list = [val for val in dict_[key].values()]
                        self.download_list_files.append(temp_list)
                    except AttributeError:
                        QtWidgets.QMessageBox.warning(self, "Ошибка", f"Неправильный запрос")

            for row in range(len(self.download_list_files)):
                stm.setItem(row, 0, QtGui.QStandardItem(str(row + 1)))
                stm.setItem(row, 1, QtGui.QStandardItem(self.download_list_files[row][0]))
                stm.setItem(row, 2, QtGui.QStandardItem(self.download_list_files[row][1]))
                stm.setItem(row, 3, QtGui.QStandardItem("Скачать"))
            self.ui.tableView.setModel(stm)
            self.ui.tableView.setItemDelegateForColumn(3, self.openDelegate)



        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Неправильный номер запроса")

    def delete_files(self):
        """
        Удаление отправки.
        Отправка delete запроса, при нажатии "Удалить"
        """
        source = self.ui.getinfoline.text()
        reply = QtWidgets.QMessageBox.question(self, 'Удалить файлы?',
                                               f'Удалить запрос {source} и его файлы из хранилища?',
                                               QtWidgets.QMessageBox.Yes,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            requests.delete(f"{self.url}/frames/{source}")

    def download_file(self, item: QtCore.QModelIndex):
        """
        Скачать один выбранный файл
        """
        file_name = self.download_list_files[item.row()][0]
        fname, ok = QtWidgets.QFileDialog.getSaveFileName(self, "Save as", file_name)
        if not ok:
            return
        directory_file = fname.replace(fname.split('/')[-1], "")
        source = self.ui.getinfoline.text()
        resp = requests.get(f"{self.url}/bucket/{source}")
        bucket_name = resp.json()['bucket_name']
        client.fget_object(bucket_name, file_name, f"{fname}")
        QtWidgets.QMessageBox.information(self, "Успешно", f"{file_name} \nЗагружен в \n{directory_file}")

    def save_all_files(self):
        """
        Сохранение всех файлов в указанную директорию
        """
        # Получаем путь, куда будем сохранять файлы
        fname = QtWidgets.QFileDialog.getExistingDirectoryUrl(self, "Save as").url()[8:]
        try:
            source = self.ui.getinfoline.text()
            resp = requests.get(f"{self.url}/bucket/{source}")  # Получаем название корзины с сервиса
            for item in self.download_list_files:
                # Сохраняем все файлы
                client.fget_object(resp.json()['bucket_name'], item[0], f"{fname}/{item[0]}")
            # В зависимости от количества файлов, выдаем информационное сообщение в нужном исчислении
            if len(self.download_list_files) == 1:
                QtWidgets.QMessageBox.information(self, "Успешно", f"1 файл загружен в {fname}")
            elif 1 < len(self.download_list_files) < 5:
                QtWidgets.QMessageBox.information(self, "Успешно",
                                                  f"{len(self.download_list_files)} файла загружены в {fname}")
            else:
                QtWidgets.QMessageBox.information(self, "Успешно",
                                                  f"{len(self.download_list_files)} файлов загружены в {fname}")
        except:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Ошибка загрузки")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Эвент на закрытие приложения
        """
        reply = QtWidgets.QMessageBox.question(self, 'Закрыть окно?', 'Вы хотите закрыть окно?',
                                               QtWidgets.QMessageBox.Yes,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


class AboutWindow(QtWidgets.QWidget):
    """
    Окно About
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.initUi()

    def initUi(self):
        self.textarea = QtWidgets.QLabel("Отправляем файлы в min.io и записываем в sqlite\n")
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.textarea)
        self.setLayout(main_layout)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    win = MainWindow()
    win.show()

    app.exec_()
