import sys
import time
import threading
import os
from multiprocessing import Process, Lock, Manager, Queue

from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import *


root_path = os.path.abspath(os.path.dirname('__file__'))

################################################
#######创建主窗口
################################################
class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('My Browser')  # 窗口标题
        self.setGeometry(5, 30, 1355, 730)  # 设置初始窗口位置坐标（左上，右下）

        self.showMaximized()  # 最大化
        self.setWindowFlags(Qt.FramelessWindowHint)  # 隐藏标题栏
        self.webview = WebEngineView()  # 浏览器初始化
        print(root_path)
        # 开启进入初始界面
        url = root_path + r"/mirror_system/Web_Project/index.html"
        url = url.replace('\\', '/')  # url
        print(url)

        self.webview.load(QUrl(url))
        self.setCentralWidget(self.webview)


################################################
#######创建浏览器
################################################
class WebEngineView(QWebEngineView):
    windowList = []

    # 重写createwindow()
    def createWindow(self, QWebEnginePage_WebWindowType):
        new_webview = WebEngineView()
        new_window = MainWindow()
        new_window.setCentralWidget(new_webview)
        # new_window.show()
        self.windowList.append(new_window)  # 注：没有这句会崩溃！！！
        return new_webview


################################################
#######程序入门
################################################

class qt_main:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.w = MainWindow()

    def exec(self):
        self.w.show()
        self.app.exec_()

    def js_Callback(self, result):
        print(result)

    def changeSize(self, width):
        self.w.webview.page().runJavaScript(f'widthAdd({width});')

    def movePos(self, x, y):
        self.w.webview.page().runJavaScript(f'movePos({x}, {y});')

    def proRate(self, id_name, rate):
        self.w.webview.page().runJavaScript(f'pro_rate("{id_name}", {rate});')

    def location(self, page_name):
        self.w.webview.page().runJavaScript(f'window.location.href="{page_name}.html";')

def changeValue(obj, lk, q):
    while True:
        with lk:
            info = q.get()
            if info['isChange']:
                if info['name'] == 'Size': # 大小
                    value = info['value']
                    obj.changeSize(value)
                elif info['name'] == 'Pos': # 位置偏移
                    x, y = value = info['value']
                    obj.movePos(x, y)
                elif info['name'] == 'pro_rate': # 处理进度
                    id_name, rate = value = info['value']
                    print(id_name, rate)
                    obj.proRate(id_name, rate)
                elif info['name'] == 'location': # 重定位
                    value = info['value']
                    obj.location(value)


def runWindow(lk, q):
    Ball = qt_main()
    Ball.w.webview.page().runJavaScript('123;')
    t2 = threading.Thread(target=changeValue, args=(Ball, lk, q))
    t2.start()
    Ball.exec()


def main(lk, q):
    t1 = Process(target=runWindow, args=(lk, q))
    t1.start()
    t1.join()



if __name__ == '__main__':
    lock = Lock()
    m = Queue()
    main(lock, m)
    print(123145)
