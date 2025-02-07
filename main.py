import os
import sys

import CONST
from PyQt5.QtWidgets import QApplication

from main_window import MainWindow


def init_workpath():
    if hasattr(sys, 'frozen'):
        # 如果程序是frozen为True，则说明当前程序是pyinstaller打包后的exe文件
        # 获取当前程序所在目录
        current_path = os.path.dirname(sys.executable)
    else:
        # 如果程序不是frozen为False，则说明当前程序是python文件
        # 获取当前程序所在目录
        current_path = os.path.dirname(os.path.abspath(__file__))
    # 设置当前程序所在目录为工作目录
    os.chdir(current_path)

def init_path():
    # 添加系统路径
    if not os.path.exists(CONST.TEMP_DIR):
        os.makedirs(CONST.TEMP_DIR)
    if not os.path.exists(CONST.OUTPUTS_DIR):
        os.makedirs(CONST.OUTPUTS_DIR)

def init():
    init_workpath()
    init_path()


if __name__ == '__main__':
    init()
    # 固定的，PyQt5程序都需要QApplication对象。sys.argv是命令行参数列表，确保程序可以双击运行
    app = QApplication(sys.argv)
    # 初始化窗口
    main_win = MainWindow()
    # main_win.resize(1000, 750)  # 设置窗体的宽为800像素，高为600像素
    # # 显示ui界面
    main_win.show()
    # 程序运行，sys.exit方法确保程序完整退出。
    sys.exit(app.exec_())
