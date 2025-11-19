#!/usr/bin/env python3
"""
Main window for the Audio Recorder and Renderer Tool.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QFrame, QSizePolicy
)
from PySide6.QtGui import QPalette, QColor, QFont
from PySide6.QtCore import Qt, QTimer
from audio_tool.audio import AudioRecorder
from .waveform_widget import WaveformWidget


class MainWindow(QMainWindow):
    """
    Main window class for the Audio Recorder and Renderer Tool.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Recorder & Renderer")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize audio recorder
        self.recorder = AudioRecorder()
        
        # Initialize UI components
        self.init_ui()
        
        # Connect signals and slots
        self.connect_signals()
        
        # Load available microphones
        self.load_microphones()
        
    def init_ui(self):
        """
        Initialize the user interface components.
        """
        # Create central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title label
        title_label = QLabel("Audio Recorder & Renderer", self)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Control buttons layout
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        
        # Microphone selection with dropdown
        mic_layout = QHBoxLayout()
        mic_layout.setSpacing(5)
        
        self.mic_label = QLabel("麦克风:", self)
        mic_layout.addWidget(self.mic_label)
        
        self.mic_combo = QComboBox(self)
        self.mic_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # TODO: Populate with available microphones
        self.mic_combo.addItem("默认麦克风")
        mic_layout.addWidget(self.mic_combo)
        
        controls_layout.addLayout(mic_layout, 1)
        
        # Record button
        self.record_button = QPushButton("开始录音", self)
        self.record_button.setStyleSheet(
            "QPushButton { background-color: #FF6B6B; color: white; font-weight: bold; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #FF5252; }"
        )
        controls_layout.addWidget(self.record_button)
        
        # Play button
        self.play_button = QPushButton("播放录音", self)
        self.play_button.setStyleSheet(
            "QPushButton { background-color: #4ECDC4; color: white; font-weight: bold; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #26A69A; }"
        )
        self.play_button.setEnabled(False)  # Disabled initially
        controls_layout.addWidget(self.play_button)
        
        main_layout.addLayout(controls_layout)
        
        # Render area
        render_frame = QFrame(self)
        render_frame.setFrameShape(QFrame.StyledPanel)
        render_frame.setFrameShadow(QFrame.Raised)
        render_frame.setStyleSheet(
            "QFrame { background-color: #F7F9FC; border: 2px solid #E1E8ED; border-radius: 5px; }"
        )
        render_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.render_layout = QVBoxLayout(render_frame)
        self.render_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create waveform rendering widget
        self.waveform_widget = WaveformWidget()
        self.waveform_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.render_layout.addWidget(self.waveform_widget)
        
        main_layout.addWidget(render_frame)
        
        # Recording timer
        self.recording_timer = QTimer(self)
        self.recording_time = 0
        self.recording_timer.timeout.connect(self.update_recording_time)
        
        # Status bar
        self.status_label = QLabel("就绪", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("QLabel { color: #1DA1F2; font-weight: bold; }")
        main_layout.addWidget(self.status_label)
        
    def update_status(self, message):
        """
        Update the status bar with the given message.
        """
        self.status_label.setText(message)
        
    def update_microphone_list(self, microphones):
        """
        Update the microphone dropdown list with available microphones.
        """
        self.mic_combo.clear()
        for mic in microphones:
            self.mic_combo.addItem(mic["name"], mic["index"])
        
    def connect_signals(self):
        """
        Connect signals and slots for UI components and audio recorder.
        """
        # UI signals
        self.record_button.clicked.connect(self.toggle_recording)
        self.play_button.clicked.connect(self.toggle_playback)
        
        # Audio recorder signals
        self.recorder.recording_started.connect(self.on_recording_started)
        self.recorder.recording_stopped.connect(self.on_recording_stopped)
        self.recorder.error_occurred.connect(self.on_error_occurred)
        self.recorder.audio_data_available.connect(self.on_audio_data_available)
        self.recorder.playing_started.connect(self.on_playing_started)
        self.recorder.playing_stopped.connect(self.on_playing_stopped)
    
    def load_microphones(self):
        """
        Load available microphones into the dropdown menu.
        """
        microphones = self.recorder.get_available_microphones()
        self.update_microphone_list(microphones)
        
        if microphones:
            self.update_status(f"发现 {len(microphones)} 个麦克风")
        else:
            self.update_status("未发现麦克风")
    
    def toggle_recording(self):
        """
        Toggle recording state when the record button is clicked.
        """
        selected_mic = self.get_selected_microphone()
        
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        else:
            # Clear previous recording and waveform
            self.recorder.stop_recording()
            self.waveform_widget.clear_waveform()
            self.recorder.start_recording(selected_mic)
    
    def on_recording_started(self):
        """
        Handle recording started event.
        """
        self.record_button.setText("停止录音")
        self.record_button.setStyleSheet(
            "QPushButton { background-color: #4ECDC4; color: white; font-weight: bold; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #26A69A; }"
        )
        self.mic_combo.setEnabled(False)
        self.play_button.setEnabled(False)
        self.update_status("正在录音...")
        
        # Start recording timer
        self.recording_time = 0
        self.recording_timer.start(1000)
    
    def on_recording_stopped(self):
        """
        Handle recording stopped event.
        """
        self.record_button.setText("开始录音")
        self.record_button.setStyleSheet(
            "QPushButton { background-color: #FF6B6B; color: white; font-weight: bold; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #FF5252; }"
        )
        self.mic_combo.setEnabled(True)
        self.play_button.setEnabled(True)
        
        # Stop recording timer
        self.recording_timer.stop()
        
        duration = self.recorder.get_recording_duration()
        self.update_status(f"录音完成，时长: {duration:.2f} 秒")
    
    def toggle_playback(self):
        """
        Toggle playback state when the play button is clicked.
        """
        if self.recorder.is_playing:
            self.recorder.stop_playback()
        else:
            self.recorder.play_recording()
    
    def on_playing_started(self):
        """
        Handle playback started event.
        """
        self.play_button.setText("停止播放")
        self.play_button.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        self.record_button.setEnabled(False)
        self.mic_combo.setEnabled(False)
        self.update_status("正在播放...")
    
    def on_playing_stopped(self):
        """
        Handle playback stopped event.
        """
        self.play_button.setText("播放录音")
        self.play_button.setStyleSheet(
            "QPushButton { background-color: #4ECDC4; color: white; font-weight: bold; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #26A69A; }"
        )
        self.record_button.setEnabled(True)
        self.mic_combo.setEnabled(True)
        self.update_status("播放完成")
    
    def on_error_occurred(self, error_message):
        """
        Handle error events from the audio recorder.
        """
        self.update_status(f"错误: {error_message}")
    
    def on_audio_data_available(self, audio_data):
        """
        Handle new audio data available event and update waveform.
        """
        if self.recorder.is_recording:
            self.waveform_widget.update_audio_data(audio_data)
    
    def update_recording_time(self):
        """
        Update the recording time displayed in the status bar.
        """
        self.recording_time += 1
        minutes = self.recording_time // 60
        seconds = self.recording_time % 60
        self.status_label.setText(f"正在录音... {minutes:02d}:{seconds:02d}")
    
    def get_selected_microphone(self):
        """
        Get the index of the selected microphone.
        """
        return self.mic_combo.currentData()