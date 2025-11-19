import sys
import time
from loguru import logger
import wave

from PySide6.QtCore import QThread, Signal, QObject
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QSizePolicy, QMessageBox

import pyaudio


class Worker(QObject):
    finished_signal = Signal()
    progress_signal = Signal(int)

    # 录音参数
    FORMAT = pyaudio.paInt16  # 音频格式
    CHANNELS = 1  # 单声道
    RATE = 48000  # 采样率
    CHUNK = 1000  # 数据块大小
    RECORD_SECONDS = 10  # 录音时长
    WAVE_OUTPUT_FILENAME = "output.wav"  # 临时WAV文件名

    def __init__(self, idx):
        super().__init__()
        self._is_running = True
        self.device_index = idx

    def stop(self):
        logger.info("stop 1")
        if not self._is_running:
            logger.warning("not running!! can not stop")
            return
        logger.info("stop 2")
        self._is_running = False
        logger.info("stop 3")

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
                self.progress_signal.emit(int(duration))

    def do_work_run(self):
        try:
            self.do_work()
        except Exception as e:
            logger.error(f"录音过程中发生错误: {str(e)}")
            return

        self.finished_signal.emit()

    def do_work(self):
        logger.info("开始录音...")
        self.pa = pyaudio.PyAudio()
        if not self.open_wave(self.WAVE_OUTPUT_FILENAME):
            logger.error("打开WAV文件失败")
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
        logger.info("bye from thread")


class MainDialog(QWidget):

    LABEL_NOT_RUNNING = "线程状态: 未运行"
    LABEL_RUNNING = "线程状态: 运行中"
    LABEL_FINISHED = "线程状态: 已完成"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Capture")

        self.label_status = QLabel(self.LABEL_NOT_RUNNING)
        self.label_progress = QLabel("进度: 0")


        layout = QVBoxLayout()

        mic_layout = QHBoxLayout()
        self.mic_label = QLabel("麦克风:", self)
        mic_layout.addWidget(self.mic_label)

        self.mic_combo = QComboBox(self)
        self.mic_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        mp = self.get_available_microphones()
        self.update_microphone_list(mp)

        # self.mic_combo.currentIndexChanged.connect(self.on_mic_selected)
        if self.mic_combo.count() > 0:
            self.mic_combo.setCurrentIndex(0)
        
        # TODO: Populate with available microphones
        # self.mic_combo.addItem("默认麦克风")
        mic_layout.addWidget(self.mic_combo)

        layout.addLayout(mic_layout)
        layout.addStretch(1)

        hl2 = QHBoxLayout()
        self.btnStart = QPushButton("Start")
        self.btnStop = QPushButton("Stop")
        hl2.addWidget(self.btnStart)
        hl2.addWidget(self.btnStop)

        layout.addWidget(self.label_progress)
        layout.addWidget(self.label_status)

        layout.addLayout(hl2)
        
        self.setLayout(layout)

        self.btnStart.clicked.connect(self.start_thread)
        self.btnStop.clicked.connect(self.stop_thread)
        self.update_status(self.LABEL_NOT_RUNNING)

    def update_microphone_list(self, microphones):
        """
        Update the microphone dropdown list with available microphones.
        """
        self.mic_combo.clear()
        for mic in microphones:
            self.mic_combo.addItem(mic["name"], mic["index"])

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
            logger.error(f"获取麦克风列表失败: {str(e)}")
            microphones.append({'index': 0, 'name': '默认麦克风'})

        return microphones

    def get_selected_microphone(self):
        """
        Get the selected microphone index.
        
        Returns:
            int: Index of the selected microphone, or None if no selection
        """
        return self.mic_combo.currentData()

    def update_status(self, status):
        if status == self.LABEL_RUNNING:
            self.btnStart.setText("Stop Thread")
        else:
            self.btnStart.setText("Start Thread")
        self.btnStop.setEnabled(status == self.LABEL_RUNNING)

        self.label_status.setText(status)

    def stop_thread(self):
        self.update_status(self.LABEL_NOT_RUNNING)
        if self.thread.isRunning():
            self.worker.stop()
            self.thread.quit()
            self.thread.wait()

        # self.worker = None
        logger.info("线程已停止")
        self.btnStart.setEnabled(True)

    def start_thread(self):
        selected_mic = self.get_selected_microphone()
        if selected_mic is None:
            QMessageBox.warning(self, "警告", "请选择麦克风")
            return

        self.btnStart.setEnabled(False)

        self.worker = Worker(selected_mic)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.do_work_run)
        self.thread.finished.connect(self.stop_thread)
        self.worker.progress_signal.connect(self.on_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.thread.start()

        self.update_status(self.LABEL_RUNNING)

    def on_finished(self):
        self.thread.quit()
        self.thread.wait()
        self.update_status(self.LABEL_FINISHED)
        self.btnStart.setEnabled(True)

    def on_progress(self, value):
        self.label_progress.setText(f"进度: {value}")


if __name__ == "__main__":
    logger.remove()
    logger.add("audio.log", level="INFO")
    logger.add(sys.stderr, level="INFO")
    app = QApplication(sys.argv)
    demo = MainDialog()
    demo.show()
    sys.exit(app.exec())