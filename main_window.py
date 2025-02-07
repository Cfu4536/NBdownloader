import queue
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Thread

import CONST
import tools
from PyQt5.QtGui import QIcon, QFont, QKeySequence, QCursor, QStandardItemModel, QStandardItem, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QAction, QFrame, QLabel, QWidget, \
    QTextEdit, QShortcut, QDialog, QMessageBox, QTableView
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5 import QtCore, QtWidgets

from UI.main_window import Ui_MainWindow
from dialog_choose_bili import DialogChooseBili
from reqs.Bilibili import Bilibili


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("NB下载器")
        self.stop_thread = False
        # 测试用！！！！！！！！！！！！！！
        self.lineEdit_url_bili.setText(
            "https://www.bilibili.com/video/BV1bv4y1W7E3/?spm_id_from=333.788.videopod.sections&vd_source=e8d2cce76bd77ea6b770f6cfe4f976db")

        # button
        self.pushButton_submit_bili.clicked.connect(self.submit_bili)

        # tableView model
        self.model_bili = QStandardItemModel(self.tableView_bili)
        self.model_bili.setHorizontalHeaderLabels(['名称', '状态', '大小', '速度'])
        self.tableView_bili.setModel(self.model_bili)
        self.setColumnWidths(self.tableView_bili, [0.4, 0.15, 0.25, 0.15])
        self.tableView_bili.setSelectionBehavior(QTableView.SelectRows)  # 设置选择行为，使其不可选择
        self.tableView_bili.setSelectionMode(QTableView.NoSelection)  # 设置选择行为，使其不可选择

        # downloader
        self.Bili_downloader = Bilibili(is_UI=True)

        # 刷新
        self.freq = 0.5
        self.refresh_thread = RefreshThread()
        self.refresh_thread.set_freq(self.freq)
        self.refresh_thread.update_signal.connect(self.refresh_table)
        self.refresh_thread.start()
        self.executor = ThreadPoolExecutor(max_workers=CONST.MAX_THREADS)

    def submit_bili(self):
        url_domain = self.lineEdit_url_bili.text()

        if url_domain and "www.bilibili.com" in url_domain:
            title, page_list = self.Bili_downloader.get_video(url_domain)
            if title:
                intent = {
                    'title': title,
                    'bvid': tools.extract_bvid(url_domain),
                    'max_quality': self.Bili_downloader.max_quality,
                    'accept_option': self.Bili_downloader.accept_option,
                    'page_list': page_list
                }
                dialog = DialogChooseBili(intent)  # 创建对话框实例
                if dialog.exec_() == QDialog.Accepted:  # 如果对话框是通过确认按钮关闭的
                    self.Bili_downloader.remove_task(title)
                    return_info = dialog.get_return_data()  # 接收返回数据
                    accept_id = return_info['accept_id']
                    page_list = return_info['page_list']
                    Thread(target=self.up_thread_pool, args=(page_list, url_domain, accept_id)).start()
                else:
                    self.Bili_downloader.remove_task(title)
                    return
        else:
            return

    ###################功能函数####################
    def updata_table(self):
        '''
        更新表中内容
        :return:
        '''
        self.model_bili.removeRows(0, self.model_bili.rowCount())
        task_info = self.Bili_downloader.get_task_info()

        for title, info in task_info.items():
            task_size_d = task_info[title]['size'] - task_info[title].get('last_size', 0)
            task_info[title]['last_size'] = task_info[title]['size']

            task_name_item = QStandardItem(title)
            task_state_item = QStandardItem(task_info[title]['status'])
            task_size_item = QStandardItem(str(task_info[title]['size_ratio']))
            task_speed_item = QStandardItem(tools.format_size(int(task_size_d / self.freq)) + '/s')

            task_state_item.setTextAlignment(Qt.AlignCenter)
            task_size_item.setTextAlignment(Qt.AlignCenter)
            task_speed_item.setTextAlignment(Qt.AlignCenter)

            self.model_bili.appendRow([task_name_item, task_state_item, task_size_item, task_speed_item])

    def refresh_table(self, size_freq):
        '''
        线程操作，刷新表格
        :return:
        '''
        # self.model_bili.removeRows(0, self.model_bili.rowCount())
        task_info = self.Bili_downloader.get_task_info()

        for index, (title, info) in enumerate(task_info.items()):
            if index >= self.model_bili.rowCount():
                break
            task_size_d = task_info[title]['size'] - task_info[title].get('last_size', 0)
            task_info[title]['last_size'] = task_info[title]['size']

            task_name_item = QStandardItem(title)
            task_state_item = QStandardItem(task_info[title]['status'])
            task_size_item = QStandardItem(str(task_info[title]['size_ratio']))
            task_speed_item = QStandardItem(tools.format_size(int(task_size_d / size_freq)) + '/s')

            task_state_item.setTextAlignment(Qt.AlignCenter)
            task_size_item.setTextAlignment(Qt.AlignCenter)
            task_speed_item.setTextAlignment(Qt.AlignCenter)

            if task_info[title]['status'] == '失败':
                task_state_item.setBackground(QColor(254, 106, 103, 50))
            elif task_info[title]['status'] == '完成':
                task_state_item.setBackground(QColor(100, 127, 83, 50))
            elif task_info[title]['status'] != '等待中':
                task_state_item.setBackground(QColor(222, 179, 52, 50))

            self.model_bili.setItem(index, 0, task_name_item)
            self.model_bili.setItem(index, 1, task_state_item)
            self.model_bili.setItem(index, 2, task_size_item)
            self.model_bili.setItem(index, 3, task_speed_item)

    def up_thread_pool(self, page_list, url_domain, accept_id):
        for bvid, _, p in page_list:
            url_page = tools.replace_bvid(url=url_domain, new_bvid=bvid)
            url_page = tools.modify_url_parameter(url=url_page, param_name="p", new_value=p)
            title, _ = self.Bili_downloader.get_video(url_page)
            audio_url, video_url = self.Bili_downloader.get_video_url(accept_id)
            self.updata_table()
            # Thread(target=self.Bili_downloader.download, args=(audio_url, video_url, title)).start()
            self.executor.submit(self.Bili_downloader.download, audio_url, video_url, title)

    ###################基本函数####################

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '确认退出',
                                     '你确定要退出吗?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.executor.shutdown(wait=False)
            self.stop_thread = True
            event.accept()  # 关闭窗口
        else:
            event.ignore()  # 忽略关闭事件

    def sentMessage(self, title, content):
        '''
        发送通知
        :param title: 标题
        :param content: 内容
        :return:
        '''
        self.tray_icon.showMessage(title, content, QSystemTrayIcon.Information, 1000)

    def setColumnWidths(self, table_view, ratios):
        '''
        设置表格列宽
        :param table_view:
        :param ratios:
        :return:
        '''
        total_width = 700
        for i, ratio in enumerate(ratios):
            column_width = int(total_width * ratio)
            table_view.setColumnWidth(i, column_width)


class RefreshThread(QThread):
    # 定义一个信号，用于发送更新的数据
    update_signal = pyqtSignal(int)
    freq = 0.5

    def set_freq(self, freq):
        self.freq = freq

    def run(self):
        while True:
            # 模拟一些处理时间

            time.sleep(self.freq)
            # 发送信号，更新第 i 行的数据
            self.update_signal.emit(self.freq)
