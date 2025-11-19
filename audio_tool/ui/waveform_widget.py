#!/usr/bin/env python3
"""
Waveform visualization widget for audio data.
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QBrush
from PySide6.QtCore import Qt, QPointF
import numpy as np


class WaveformWidget(QWidget):
    """
    Widget that displays audio waveform in real-time.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration
        self.background_color = Qt.white
        self.waveform_color = Qt.black
        self.axis_color = Qt.gray
        self.padding = 20
        
        # Audio data buffer (for visualization)
        self.audio_buffer = np.array([], dtype=np.int16)
        self.max_buffer_size = 44100  # Store up to 1 second of data at 44.1kHz
        
        # Scale factor for normalization
        self.max_amplitude = 32767  # Maximum value for int16 audio
        
        # Set widget properties
        self.setMinimumSize(200, 150)
    
    def update_audio_data(self, new_data):
        """
        Update the audio buffer with new data and refresh the waveform.
        
        Args:
            new_data (numpy.ndarray): New audio data to add to the buffer
        """
        # Add new data to the buffer
        self.audio_buffer = np.concatenate((self.audio_buffer, new_data))
        
        # Keep the buffer size within limits
        if len(self.audio_buffer) > self.max_buffer_size:
            self.audio_buffer = self.audio_buffer[-self.max_buffer_size:]
        
        # Refresh the display
        self.update()
    
    def clear_waveform(self):
        """
        Clear the audio buffer and refresh the display.
        """
        self.audio_buffer = np.array([], dtype=np.int16)
        self.update()
    
    def paintEvent(self, event):
        """
        Paint the waveform on the widget.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        
        # Fill background
        painter.fillRect(0, 0, width, height, QBrush(self.background_color))
        
        # Draw axes
        painter.setPen(QPen(self.axis_color, 1))
        
        # Horizontal axis (center line)
        center_y = height / 2
        painter.drawLine(self.padding, center_y, width - self.padding, center_y)
        
        # Vertical axes
        painter.drawLine(self.padding, self.padding, self.padding, height - self.padding)
        painter.drawLine(width - self.padding, self.padding, width - self.padding, height - self.padding)
        
        # Draw waveform if there is data
        if len(self.audio_buffer) > 0:
            self._draw_waveform(painter, width, height)
    
    def _draw_waveform(self, painter, width, height):
        """
        Draw the audio waveform.
        
        Args:
            painter (QPainter): Painter object
            width (int): Widget width
            height (int): Widget height
        """
        # Calculate available space
        available_width = width - 2 * self.padding
        available_height = height - 2 * self.padding
        
        # Scale factor for x-axis (time)
        x_scale = available_width / len(self.audio_buffer)
        
        # Scale factor for y-axis (amplitude)
        y_scale = available_height / (2 * self.max_amplitude)
        
        # Create pen for waveform
        pen = QPen(self.waveform_color, 1.5)
        painter.setPen(pen)
        
        # Draw the waveform as a polyline
        center_y = height / 2
        
        # If we have too many points, downsample for better performance
        if len(self.audio_buffer) > 1000:
            downsample_factor = len(self.audio_buffer) // 1000
            downsampled_data = self.audio_buffer[::downsample_factor]
            x_scale *= downsample_factor
        else:
            downsampled_data = self.audio_buffer
        
        # Create list of points for the polyline
        points = []
        for i, sample in enumerate(downsampled_data):
            x = self.padding + i * x_scale
            y = center_y - sample * y_scale
            points.append((x, y))
        
        # Draw the polyline
        if points:
            # Convert tuples to QPointF objects
            qpoints = [QPointF(x, y) for x, y in points]
            painter.drawPolyline(qpoints)
    
    def update_waveform_color(self, color):
        """
        Update the color of the waveform.
        
        Args:
            color (Qt.Color): New color for the waveform
        """
        self.waveform_color = color
        self.update()
    
    def update_background_color(self, color):
        """
        Update the background color of the widget.
        
        Args:
            color (Qt.Color): New background color
        """
        self.background_color = color
        self.update()