import sys
import time
from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QProgressBar, QTextEdit


class Worker(QObject):
    """工作线程类"""
    progress_signal = Signal(int)  # 进度信号
    message_signal = Signal(str)   # 消息信号
    finished_signal = Signal()     # 完成信号
    
    def __init__(self):
        super().__init__()
        self._is_running = True
    
    def stop(self):
        """停止工作"""
        self._is_running = False
    
    def do_work(self):
        """执行后台任务"""
        try:
            for i in range(1, 101):
                if not self._is_running:
                    self.message_signal.emit("任务被用户中断")
                    break
                
                # 模拟耗时任务
                time.sleep(0.1)
                
                # 更新进度
                self.progress_signal.emit(i)
                self.message_signal.emit(f"处理进度: {i}%")
            
            if self._is_running:
                self.message_signal.emit("任务完成")
            self.finished_signal.emit()
                
        except Exception as e:
            self.message_signal.emit(f"发生错误: {str(e)}")
            self.finished_signal.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_thread()
    
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("可中断的后台任务示例")
        self.setGeometry(100, 100, 400, 300)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        self.start_btn = QPushButton("开始任务")
        self.stop_btn = QPushButton("停止任务")
        self.stop_btn.setEnabled(False)
        
        self.progress_bar = QProgressBar()
        self.text_edit = QTextEdit()
        
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.text_edit)
        
        central_widget.setLayout(layout)
        
        # 连接信号
        self.start_btn.clicked.connect(self.start_task)
        self.stop_btn.clicked.connect(self.stop_task)
    
    def setup_thread(self):
        """设置工作线程"""
        self.worker = Worker()
        self.thread = QThread()
        
        # 将worker移动到线程中
        self.worker.moveToThread(self.thread)
        
        # 连接信号
        self.thread.started.connect(self.worker.do_work)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.message_signal.connect(self.append_message)
        self.worker.finished_signal.connect(self.on_task_finished)
    
    def start_task(self):
        """开始任务"""
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.text_edit.clear()
        
        self.worker._is_running = True
        self.thread.start()
    
    def stop_task(self):
        """停止任务"""
        self.worker.stop()
        self.stop_btn.setEnabled(False)
    
    def on_task_finished(self):
        """任务完成处理"""
        self.thread.quit()
        self.thread.wait()
        self.start_btn.setEnabled(True)
    
    def append_message(self, message):
        """添加消息到文本框"""
        self.text_edit.append(f"[{time.strftime('%H:%M:%S')}] {message}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.thread.isRunning():
            self.worker.stop()
            self.thread.quit()
            self.thread.wait(3000)  # 等待3秒
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())