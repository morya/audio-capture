#!/usr/bin/env python3
"""
Audio recording functionality using PyAudio library.
"""

from loguru import logger

import pyaudio
import numpy as np
import wave
import time
from PySide6.QtCore import QThread, Signal, QObject


class WaveWriter:

    def __init__(self, fn: str):
        self.fn = fn
        self.CHANNELS = 1  # Mono recording
        self.RATE = 44100  # Sampling rate (Hz)
        self.FORMAT = pyaudio.paInt16  # Sample format

    def init(self, sw, fn: str = None):
        if fn is None:
            fn = self.fn
        try:
            self.w = wave.open(fn, 'wb')
            self.w.setnchannels(self.CHANNELS)
            self.w.setsampwidth(sw)
            self.w.setframerate(self.RATE)
        except Exception as e:
            print(f"Error initializing wave file: {e}")
            raise e

    def write(self, data: bytes):
        """
        Write audio data to the wave file.
        
        Args:
            data (bytes): Audio data to write
        """
        self.w.writeframes(data)
        # self.recording_file_size += len(data)
    
    def close(self):
        self.w.close()


class AudioRecorder(QObject):
    """
    Audio recorder class that handles microphone input and recording functionality.
    """
    
    # Signals for communication with UI
    audio_data_available = Signal(np.ndarray)  # Emitted when new audio data is available

    thread_started = Signal()  # Emitted when recording thread starts
    thread_stopped = Signal()  # Emitted when recording thread stops

    recording_started = Signal()  # Emitted when recording starts
    recording_stopped = Signal()  # Emitted when recording stops
    error_occurred = Signal(str)  # Emitted when an error occurs
    playing_started = Signal()  # Emitted when playback starts
    playing_stopped = Signal()  # Emitted when playback stops
    
    def __init__(self):
        super().__init__()
        
        # Audio parameters
        self.CHUNK = 1024  # Number of frames per buffer
        self.FORMAT = pyaudio.paInt16  # Sample format
        self.CHANNELS = 1  # Mono recording
        self.RATE = 44100  # Sampling rate (Hz)
        
        # PyAudio instance
        self.pa = pyaudio.PyAudio()
        
        # Recording state
        self.is_recording = False
        self.stream = None

        self.recording_file_size = 1024 * 1024 * 5  # 2MB

        self.MAX_FILE_SIZE = 1024 * 1024 * 20  # 100MB
        
        # Recording thread
        self.record_thread = None
        
        # Playback state
        self.is_playing = False
        self.play_thread = None
    
    def get_available_microphones(self):
        """
        Get a list of available microphones.
        
        Returns:
            list: List of dictionaries containing microphone information (index, name)
        """
        microphones = []
        
        try:
            for i in range(self.pa.get_device_count()):
                device_info = self.pa.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # Only input devices (microphones)
                    microphones.append({
                        'index': i,
                        'name': device_info['name']
                    })
        except Exception as e:
            self.error_occurred.emit(f"获取麦克风列表失败: {str(e)}")
            microphones.append({'index': 0, 'name': '默认麦克风'})
        
        return microphones
    
    def start_recording(self, device_index=None):
        """
        Start recording audio from the selected microphone.
        
        Args:
            device_index (int, optional): Index of the microphone to use. Defaults to None (default device).
        """
        try:
            if self.is_recording:
                return
            
            self.is_recording = True
            self.recording_file_size = 0

            try:
                self.writer = WaveWriter("temp_recording.wav")
                self.writer.init(self.pa.get_sample_size(self.FORMAT))
            except Exception as e:
                self.error_occurred.emit(f"创建录音文件失败: {str(e)}")
                self.is_recording = False
                return
            
            # Open audio stream
            try:
                self.stream = self.pa.open(
                    input_device_index=device_index,
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.RATE,
                    input=True,
                    frames_per_buffer=self.CHUNK
                )
            except OSError as e:
                # Check for permission-related errors
                error_code = e.errno if hasattr(e, 'errno') else None
                if error_code in [-9996, -9997]:
                    s = f"""麦克风访问失败: 请检查麦克风权限设置。\n在 macOS 系统偏好设置中，进入"安全性与隐私" -> "隐私" -> "麦克风"，确保应用已获得授权。"""
                    self.error_occurred.emit(s)
                else:
                    self.error_occurred.emit(f"麦克风访问失败: {str(e)}")
                self.is_recording = False
                
                return
            except Exception as e:
                self.error_occurred.emit(f"打开音频流失败: {str(e)}")
                self.is_recording = False
                return
            
            # Create and start recording thread
            self.record_thread = QThread()
            self.moveToThread(self.record_thread)
            self.record_thread.started.connect(self._record_loop)
            self.recording_stopped.connect(self.record_thread.quit)
            self.record_thread.finished.connect(self.record_thread.deleteLater)
            self.record_thread.start()
            
            self.recording_started.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"开始录音失败: {str(e)}")
            self.is_recording = False

    
    def stop_recording(self):
        """
        Stop recording audio.
        """
        try:
            if not self.is_recording:
                logger.info("stop_recording: not recording")
                return
            
            logger.info("stop_recording: recording")
            self.is_recording = False

            if self.record_thread:
                # self.record_thread.quit()
                self.record_thread.wait()
                self.record_thread = None

            self.pa.terminate()
            
        except Exception as e:
            self.error_occurred.emit(f"停止录音失败: {str(e)}")
    
    def _record_loop(self):
        """
        Internal recording loop that runs in a separate thread.
        """
        logger.info("start _record_loop")
        n = int(time.time() * 20)
        self.recording_file_size = 0
        try:
            while self.is_recording:
                data = self.stream.read(self.CHUNK)
                
                # Convert binary data to numpy array
                audio_array = np.frombuffer(data, dtype=np.int16)
                
                # Store the data
                # self.recording_data.append(audio_array)

                self.writer.write(data)

                self.recording_file_size += len(data)

                if self.recording_file_size >= self.MAX_FILE_SIZE:
                    self.stop_recording()
                    break
                
                # Emit signal with new audio data
                nn = int(time.time() * 20)
                if nn - n > 1:
                    n = nn
                    self.audio_data_available.emit(audio_array)

            logger.info("stop _record_loop")

        except Exception as e:
            logger.error(f"_record_loop: 录音过程中发生错误: {str(e)}")
            self.is_recording = False
        finally:
            self.is_recording = False

        try:
            logger.info("try close writer")
            self.writer.close()
            logger.info("close writer success")
        except Exception as e:
            logger.error(f"_record_loop: 关闭录音文件失败: {str(e)}")
        finally:
            logger.info("finally _record_loop")

        logger.info("emit recording_stopped")
        self.recording_stopped.emit()
        logger.info("emit thread_stopped")
        self.thread_stopped.emit()
    
    def get_recording_data(self):
        """
        Get the recorded audio data.
        
        Returns:
            numpy.ndarray: The recorded audio data as a single numpy array.
        """
        if not self.recording_data:
            return np.array([], dtype=np.int16)
        
        return np.concatenate(self.recording_data)
    
    def get_recording_duration(self):
        """
        Get the duration of the recording in seconds.
        
        Returns:
            float: Duration in seconds
        """
        total_samples = sum(len(chunk) for chunk in self.recording_data)
        return total_samples / self.RATE
    
    def play_recording(self):
        """
        Play back the recorded audio.
        """
        try:
            if self.is_playing or not self.recording_data:
                return
            
            self.is_playing = True
            
            # Create and start playback thread
            self.play_thread = QThread()
            self.moveToThread(self.play_thread)
            self.play_thread.started.connect(self._play_loop)
            self.play_thread.start()
            
            self.playing_started.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"开始播放失败: {str(e)}")
            self.is_playing = False
    
    def stop_playback(self):
        """
        Stop playback of audio.
        """
        try:
            if not self.is_playing:
                return
            
            self.is_playing = False
            
            if self.play_thread:
                self.play_thread.quit()
                self.play_thread.wait()
                self.play_thread = None
            
            self.playing_stopped.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"停止播放失败: {str(e)}")
    
    def _play_loop(self):
        """
        Internal playback loop that runs in a separate thread.
        """
        try:
            if not self.recording_data:
                return
            
            # Open audio stream for playback
            stream = self.pa.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                output=True,
                frames_per_buffer=self.CHUNK
            )
            
            # Convert recorded data to bytes for playback
            all_data = self.get_recording_data()
            
            # Play the audio in chunks
            num_chunks = len(all_data) // self.CHUNK
            
            for i in range(num_chunks):
                if not self.is_playing:
                    break
                
                # Get chunk data
                chunk = all_data[i * self.CHUNK : (i + 1) * self.CHUNK]
                
                # Convert to bytes and write to stream
                stream.write(chunk.tobytes())
            
            # Play any remaining data
            if self.is_playing and len(all_data) % self.CHUNK > 0:
                remaining_chunk = all_data[num_chunks * self.CHUNK :]
                stream.write(remaining_chunk.tobytes())
            
            stream.stop_stream()
            stream.close()
            
            self.is_playing = False
            self.playing_stopped.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"播放过程中发生错误: {str(e)}")
            self.is_playing = False
    
    def __del__(self):
        """
        Clean up PyAudio instance when object is deleted.
        """
        try:
            # Ensure all threads are stopped
            if self.record_thread and self.record_thread.isRunning():
                self.record_thread.quit()
                self.record_thread.wait()
            
            if self.play_thread and self.play_thread.isRunning():
                self.play_thread.quit()
                self.play_thread.wait()
                
            self.pa.terminate()
        except:
            pass