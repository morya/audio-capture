import string
import pyaudio
import wave
from loguru import logger


def record_n_seconds(device_index=None, fn: string = "temp_recording.wav"):
    """
    Record audio from the selected microphone for 5 seconds.
    
    Args:
        device_index (int, optional): Index of the microphone to use. Defaults to None (default device).
    """

    try:
        w = wave.open(fn, "wb")
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
    except Exception as e:
        logger.error(f"创建WAV文件失败: {str(e)}")
        return

    try:
        # Open audio stream
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=1024,
        )

        # Record for 10 seconds
        logger.info("开始录音...")

        for i in range(5):
            logger.info(f"第{i+1}秒")
            size = 1024
            for _ in range(0, int(44100 / size)):
                data = stream.read(size)
                w.writeframes(data)
        
        w.close()
        logger.info("录音完成")

    except Exception as e:
        logger.error(f"打开麦克风失败: {str(e)}")
        return


def main():

    pa = pyaudio.PyAudio()
    print(pa.get_device_count())

    fn = "temp_recording.wav"
    for i in range(pa.get_device_count()):
        device_info = pa.get_device_info_by_index(i)
        name = 'MacBook Pro麦克风'
        if name in device_info['name']:
            print(pa.get_device_info_by_index(i))
            device_index = i
            record_n_seconds(device_index, fn)

    logger.info("bye")

    

if __name__ == "__main__":
    main()