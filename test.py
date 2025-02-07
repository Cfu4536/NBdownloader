import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QThread, pyqtSignal


class WorkerThread(QThread):
    # 定义一个信号，用于发送更新的数据
    update_signal = pyqtSignal(int)

    def run(self):
        for i in range(10):
            # 模拟一些处理时间
            time.sleep(1)
            # 发送信号，更新第 i 行的数据
            self.update_signal.emit(i)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dynamic Update in QTableView")
        self.setGeometry(200, 200, 400, 300)

        self.model = QStandardItemModel(10, 1)  # 10 行 1 列的模型
        self.model.setHorizontalHeaderLabels(['Dynamic Values'])
        for i in range(10):
            self.model.setItem(i, 0, QStandardItem(f'Initial Value {i}'))

        self.table_view = QTableView()
        self.table_view.setModel(self.model)

        self.start_button = QPushButton("Start Updating")
        self.start_button.clicked.connect(self.start_updating)

        layout = QVBoxLayout()
        layout.addWidget(self.table_view)
        layout.addWidget(self.start_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.worker_thread = WorkerThread()
        self.worker_thread.update_signal.connect(self.update_cell)

    def start_updating(self):
        self.worker_thread.start()

    def update_cell(self, row):
        self.model.setItem(row, 0, QStandardItem("dfds"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())