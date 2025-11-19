from loguru import logger
import pyaudio
import wave

# 录音参数
FORMAT = pyaudio.paInt16  # 音频格式
CHANNELS = 1  # 单声道
RATE = 44100  # 采样率
CHUNK = 1024  # 数据块大小
RECORD_SECONDS = 10  # 录音时长
WAVE_OUTPUT_FILENAME = "output.wav"  # 临时WAV文件名
MP3_OUTPUT_FILENAME = "output.mp3"  # 最终MP3文件名
TARGET_DEVICE_NAME = "MacBook Pro麦克风"  # 目标麦克风名称


def record_n_seconds(device_index: int, fn: str):
    # 初始化PyAudio
    logger.info(f"使用设备索引: {device_index}")
    audio = pyaudio.PyAudio()
    try:
        # 打开音频流
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK
        )
        
        logger.info(f"开始录音，时长: {RECORD_SECONDS}秒")
        
        frames = []  # 存储录音数据
        
        for i in range (RECORD_SECONDS):
            logger.info(f"第{i+1}秒")
            # 录音
            for i in range(0, int(RATE / CHUNK)):
                data = stream.read(CHUNK)
                frames.append(data)
        
        logger.info("录音结束")
        
        # 停止音频流
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # 保存录音到WAV文件
        wf = wave.open(fn, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
    except Exception as e:
        logger.error(f"录音过程中发生错误: {e}")
        audio.terminate()
        return


def find_device(name):
    """查找指定名称的麦克风设备索引"""
    audio = pyaudio.PyAudio()
    device_index = None
    for i in range(audio.get_device_count()):
        device_info = audio.get_device_info_by_index(i)
        if name in device_info["name"]:
            device_index = i
            print(f"找到目标麦克风: {device_info['name']}, 索引: {device_index}")
            break
    audio.terminate()
    return device_index


def main():
    # 查找目标麦克风设备
    device_index = find_device(TARGET_DEVICE_NAME)
    if device_index is None:
        logger.error(f"未找到名称包含'{TARGET_DEVICE_NAME}'的麦克风设备")
        return
    
    # 录音
    record_n_seconds(device_index, WAVE_OUTPUT_FILENAME)


if __name__ == "__main__":
    main()