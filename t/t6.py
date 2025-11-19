import sys
from loguru import logger

from PySide6.QtCore import QUrl

from PySide6.QtGui import QGuiApplication

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtWidgets import QWidget, QPushButton
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout

from PySide6.QtMultimedia import QMediaDevices, QMediaCaptureSession, QMediaRecorder, QAudioInput, QScreenCapture


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setup_connections()

    def get_default_audio_device(self):
        """获取默认音频输入设备"""
        audio_devices = QMediaDevices.audioInputs()
        if audio_devices:
            return audio_devices[0]
        return None

    def setup_media_capture(self):
        """设置媒体捕获"""
        self.capture_session = QMediaCaptureSession()

        # 获取默认音频输入设备
        default_audio_device = self.get_default_audio_device()
        if not default_audio_device:
            logger.error("No audio input devices found")
            QMessageBox.critical(self, "Error", "No audio input devices found.")
            return False
        else:
            self.audioInput = QAudioInput(default_audio_device)
            self.capture_session.setAudioInput(self.audioInput)
            logger.info(f"Using audio device: {default_audio_device.description()}")
        
        self.screenCapture = QScreenCapture()
        screen = QGuiApplication.primaryScreen()
        if not screen:
            logger.error("No screen found")
            QMessageBox.critical(self, "Error", "No screen found 11.")
            return False

        self.screenCapture.setScreen(screen)
        self.capture_session.setScreenCapture(self.screenCapture)
        s = self.screenCapture.screen()
        if not s:
            logger.error("No screen found")
            QMessageBox.critical(self, "Error", "No screen found.")
            return False
        else:
            desc = f"screen name={s.name()}, model={s.model()} "
            logger.info(f"Using screen: {desc}")

        logger.info("set recorder")
        self.recorder = QMediaRecorder()
        self.capture_session.setRecorder(self.recorder)
        self.recorder.setQuality(QMediaRecorder.NormalQuality)

        self.recorder.setOutputLocation(QUrl.fromLocalFile("output.mp4"))

        # self.audioInput.start()
        logger.info("start screen capture")
        self.screenCapture.start()
        # self.capture_session.start()
        logger.info("start recorder")
        self.recorder.record()
        return True

    def initUI(self):
        self.setWindowTitle("Media Capture")

        hbox = QHBoxLayout()
        self.btn1 = QPushButton("Start", self)
        self.btn2 = QPushButton("Stop", self)

        hbox.addWidget(self.btn1)
        hbox.addWidget(self.btn2)
        
        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.resize(300, 200)
        self.setMinimumSize(self.size())

    def start_recording(self):
        """开始录制"""
        ok = self.setup_media_capture()
        if not ok:
            return
        self.btn1.setEnabled(False)
        self.btn2.setEnabled(True)

    def stop_recording(self):
        """停止录制"""
        self.btn1.setEnabled(True)
        self.btn2.setEnabled(False)
        self.recorder.stop()
        self.screenCapture.stop()

    def setup_connections(self):
        """设置信号槽连接"""
        self.btn1.setEnabled(True)
        self.btn2.setEnabled(False)
        self.btn1.clicked.connect(self.start_recording)
        self.btn2.clicked.connect(self.stop_recording)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == "__main__":
    logger.info( "app")
    main()
