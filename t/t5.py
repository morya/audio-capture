import sys

from loguru import logger

from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtCore import QCoreApplication


def main():
    '''
    使用 QMediaDevices.audioInputs() 列出所有音频输入设备
    '''
    app = QCoreApplication(sys.argv)

    audioDevices = QMediaDevices.audioInputs()
    for device in audioDevices:
        # print("ID: {}", device.id())
        print("Description: {}".format(device.description()))
        print("Is default: {}".format(device.isDefault()))
        print("ChannelCount: min = {}, max = {}".format(device.minimumChannelCount(), device.maximumChannelCount()))
        print("SampleRate: min = {}, max = {}".format(device.minimumSampleRate(), device.maximumSampleRate()))

        print("--------")

    # app.exec()


if __name__ == "__main__":
    logger.info( "app")
    main()