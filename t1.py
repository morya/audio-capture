import sys
import time
from loguru import logger
import wave

from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QSizePolicy, QMessageBox

import pyaudio


class Worker(QObject):
    finished = Signal()
    progress = Signal(int)

    # 录音参数
    FORMAT = pyaudio.paInt16  # 音频格式
    CHANNELS = 1  # 单声道
    RATE = 48000  # 采样率
    CHUNK = 1000  # 数据块大小
    RECORD_SECONDS = 10  # 录音时长
    WAVE_OUTPUT_FILENAME = "output.wav"  # 临时WAV文件名
    TARGET_DEVICE_NAME = "MacBook Pro麦克风"  # 目标麦克风名称

    def __init__(self):
        super().__init__()
        self._is_running = False
        self.device_index = None

    def find_device(self):
        pa = pyaudio.PyAudio()
        for i in range(pa.get_device_count()):
            device_info = pa.get_device_info_by_index(i)
            name = self.TARGET_DEVICE_NAME
            if name in device_info['name']:
                logger.debug(f"找到目标麦克风: {device_info['name']} (索引: {i})")
                return i
        logger.error(f"未找到目标麦克风: {self.TARGET_DEVICE_NAME}")
        return None

    def start(self):
        if self._is_running:
            logger.warning("running!! can not start again")
            return
        self._is_running = True
        device_index = self.find_device()
        self.device_index = device_index
        
        self.t = QThread()
        self.moveToThread(self.t)
        self.finished.connect(self.t.quit)
        self.t.started.connect(self.do_work)

        self.t.start()

    def stop(self):
        if not self._is_running:
            logger.warning("not running!! can not stop")
            return
        self._is_running = False
        self.t.wait()

    def open_wave(self, fn):
        try:
            self.w = wave.open(fn, "wb")
            self.w.setnchannels(self.CHANNELS)
            self.w.setsampwidth(self.pa.get_sample_size(self.FORMAT))
            self.w.setframerate(self.RATE)
        except Exception as e:
            logger.error(f"创建WAV文件失败: {str(e)}")
            return False
        
        return True

    def close_wave(self):
        self.w.close()

    def task(self):
        chunk_size = int(self.RATE / self.CHUNK)
        s = time.time()
        while self._is_running:
            # for i in range(1, self.RECORD_SECONDS+1):
                # QThread.sleep(1)
                for _ in range(0, chunk_size):
                    data = self.stream.read(self.CHUNK)
                    # self.frames.append(data)
                    self.w.writeframes(data)
                
                n = time.time()
                duration= n - s
                logger.info(f"已录音 {duration:.2f} 秒")
                self.progress.emit(int(duration))

    def do_work(self):
        logger.info("开始录音...")
        self.pa = pyaudio.PyAudio()
        if not self.open_wave(self.WAVE_OUTPUT_FILENAME):
            logger.error("打开WAV文件失败")
            self.finished.emit()
            return

        self.stream = self.pa.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.CHUNK,
        )

        self.task()

        logger.info("录音完成")
        self.close_wave()
        self.stream.stop_stream()
        self.stream.close()
        logger.info("WAV文件已关闭")

        logger.info("PyAudio已终止")
        self.pa.terminate()
        logger.info("finished will be emitted")
        self.finished.emit()
        logger.info("bye from thread")


class ThreadExample(QWidget):

    LABEL_NOT_RUNNING = "线程状态: 未运行"
    LABEL_RUNNING = "线程状态: 运行中"
    LABEL_FINISHED = "线程状态: 已完成"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Capture")

        self.selected_mic_index = None

        self.label_status = QLabel(self.LABEL_NOT_RUNNING)
        self.label_progress = QLabel("进度: 0")
        self.button = QPushButton("Start Thread")

        layout = QVBoxLayout()

        mic_layout = QHBoxLayout()
        self.mic_label = QLabel("麦克风:", self)
        mic_layout.addWidget(self.mic_label)
        
        self.mic_combo = QComboBox(self)
        self.mic_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        mp = self.get_available_microphones()
        for m in mp:
            self.mic_combo.addItem(m['name'])
        
        self.mic_combo.currentIndexChanged.connect(self.on_mic_selected)
        
        # TODO: Populate with available microphones
        # self.mic_combo.addItem("默认麦克风")
        mic_layout.addWidget(self.mic_combo)

        layout.addLayout(mic_layout)
        layout.addStretch(1)
        layout.addWidget(self.label_progress)
        layout.addWidget(self.label_status)
        layout.addWidget(self.button)
        
        self.setLayout(layout)

        self.button.clicked.connect(self.toggle_thread)

        self.update_status(self.LABEL_NOT_RUNNING)

    def on_mic_selected(self, index):
        logger.info(f"mic selected: {index}")
        self.selected_mic_index = index

    def get_available_microphones(self):
        """
        Get a list of available microphones.
        
        Returns:
            list: List of dictionaries containing microphone information (index, name)
        """
        microphones = []
        
        pa = pyaudio.PyAudio()
        try:
            for i in range(pa.get_device_count()):
                device_info = pa.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # Only input devices (microphones)
                    microphones.append({
                        'index': i,
                        'name': device_info['name']
                    })
        except Exception as e:
            self.error_occurred.emit(f"获取麦克风列表失败: {str(e)}")
            microphones.append({'index': 0, 'name': '默认麦克风'})
        
        return microphones

    def update_status(self, status):
        if status == self.LABEL_RUNNING:
            self.button.setText("Stop Thread")
        else:
            self.button.setText("Start Thread")
        
        self.label_status.setText(status)

    def stop_thread(self):
        self.w.stop()
        self.update_status(self.LABEL_NOT_RUNNING)

    def start_thread(self):
        if self.selected_mic_index is None:
            QMessageBox.warning(self, "警告", "请选择麦克风")
            return

        self.w = Worker()
        self.w.progress.connect(self.on_progress)
        self.w.finished.connect(self.on_finished)
        self.w.start()

        self.update_status(self.LABEL_RUNNING)
    
    def toggle_thread(self):
        if self.button.text() == "Start Thread":
            self.start_thread()
        else:
            self.stop_thread()

    def on_finished(self):
        self.update_status(self.LABEL_FINISHED)

    def on_progress(self, value):
        self.label_progress.setText(f"进度: {value}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = ThreadExample()
    demo.show()
    sys.exit(app.exec())