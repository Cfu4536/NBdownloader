from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QDialog, QHeaderView, QTableView
from UI.dialog_choose_video_bili import Ui_DialogChooseBili


class DialogChooseBili(QDialog, Ui_DialogChooseBili):
    '''
        intent = {
            'title': title,
            'max_quality': max_quality,
            'accept_option': {
                accept_quality: accept_description,
            },
            'page_dict': {
                {
                 'BV1xA4m1G7uv': '幻兽帕鲁爆火，为啥挨骂的是宝可梦？？？【差评君】',
                 'BV1bv4y1W7E3': '苦不苦，看看中国汉化组，累不累，问问翻译老前辈。【差评君】',
                 'BV1cX4y1f7p7': '你可能不知道，这款40年前的游戏，它的玩法居然还在进步【差评君】',
                 'BV1Us4y1d7Bp': '用报警器来演奏？红白机时代的游戏配乐是怎样制作的？【差评君】'
                }
            }
        }
    '''

    def __init__(self, intent):
        super(DialogChooseBili, self).__init__()
        self.model_bili = None
        self.setupUi(self)

        self.intent = intent
        self.title = intent['title']
        self.bvid = intent['bvid']
        self.max_quality = intent['max_quality']
        self.accept_option = intent['accept_option']
        self.page_list = intent['page_list']
        self.return_data = {
            'accept_id': self.max_quality,  # 用户选择的最高清晰度
            'page_list': []  # 用户选择下载的视频列表
        }

        self.setWindowTitle("选择视频")
        self.label_title.setText(self.title[:self.title.rfind('_')])
        self.is_choose_all = True
        self.pushButton_choose_all_bili.setText("全不选")
        # 截断title文本
        font_metrics = self.label_title.fontMetrics()
        elided_text = font_metrics.elidedText(self.label_title.text(), Qt.ElideRight, self.label_title.width())
        self.label_title.setText(elided_text)
        # 最高清晰度
        self.label_max_qulity.setText(self.accept_option[self.max_quality])
        # 确定下载按钮和取消按钮的点击事件
        self.pushButton_download.clicked.connect(self.my_accept)
        self.pushButton_cancel.clicked.connect(self.reject)
        self.pushButton_choose_all_bili.clicked.connect(self.choose_all)

        self.init_qulity()
        self.init_page(self.page_list)

    def choose_all(self):
        if self.is_choose_all:
            for row in range(self.model_bili.rowCount()):
                item = self.model_bili.item(row, 1)
                item.setCheckState(Qt.Unchecked)
                self.pushButton_choose_all_bili.setText("全选")
                self.is_choose_all = False
        else:
            for row in range(self.model_bili.rowCount()):
                item = self.model_bili.item(row, 1)
                item.setCheckState(Qt.Checked)
                self.pushButton_choose_all_bili.setText("全不选")
                self.is_choose_all = True

    def init_qulity(self):
        max_index = 0
        for quality, description in self.intent['accept_option'].items():
            self.comboBox_qulity.addItem(description, quality)
            if quality > self.max_quality:
                max_index += 1
        self.comboBox_qulity.setCurrentIndex(max_index)

    def init_page(self, page_list):
        # tableView model
        self.model_bili = QStandardItemModel(self.tableView_choose_bili)
        self.model_bili.setHorizontalHeaderLabels(['名称', ''])
        self.tableView_choose_bili.setModel(self.model_bili)
        self.setColumnWidths(self.tableView_choose_bili, [0.85, 0.05])
        self.tableView_choose_bili.setSelectionBehavior(QTableView.SelectRows)  # 设置选择行为，使其不可选择
        self.tableView_choose_bili.setSelectionMode(QTableView.NoSelection)  # 设置选择行为，使其不可选择
        # 添加数据
        for bvid, title, p in page_list:
            title_item = QStandardItem(title)
            # 创建复选框项, 设置为可选中
            checkbox_item = QStandardItem()
            checkbox_item.setCheckable(True)
            if self.bvid == bvid:
                checkbox_item.setCheckState(Qt.Checked)  # 设置复选框状态为未选中
            else:
                checkbox_item.setCheckState(Qt.Unchecked)
            checkbox_item.setTextAlignment(Qt.AlignCenter)  # 设置复选框居中对齐
            checkbox_item.setEditable(False)
            # 添加行
            self.model_bili.appendRow([title_item, checkbox_item])

    def my_accept(self):
        for row in range(self.model_bili.rowCount()):
            item = self.model_bili.item(row, 1)
            if item.checkState() == Qt.Checked:
                self.return_data['page_list'].append((self.page_list[row][0], self.page_list[row][1], self.page_list[row][2]))
        self.accept()

    def get_return_data(self) -> dict:
        if self.comboBox_qulity.currentData():
            self.return_data['accept_id'] = self.comboBox_qulity.currentData()
        return self.return_data

    def setColumnWidths(self, table_view, ratios):
        '''
        设置表格列宽
        :param table_view:
        :param ratios:
        :return:
        '''
        total_width = 550
        header = table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)  # 设置列宽固定
        for i, ratio in enumerate(ratios):
            column_width = int(total_width * ratio)
            table_view.setColumnWidth(i, column_width)
