#!/usr/bin/env python3
"""
Main entry point for the Audio Recorder and Renderer Tool.
"""
import sys
from PySide6.QtWidgets import QApplication
from audio_tool.ui import MainWindow


class AudioRecorderApp(QApplication):
    """Main application class for the Audio Recorder and Renderer Tool."""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName("Audio Recorder & Renderer")
        self.setApplicationVersion("0.1.0")

        # Initialize main window
        self.main_window = MainWindow()
        self.main_window.show()


def main():
    """Main function to launch the application."""
    app = AudioRecorderApp(sys.argv)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())