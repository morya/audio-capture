# 代理使用说明（为 AI 编码代理准备）

目标：帮助 AI 代理快速理解并在本仓库中安全、可重复地修改与构建代码。

概要
- 本仓库是一个最小的 PySide6 GUI 音频录制示例，主要文件：`t1.py`（单文件应用）。
- 音频采集由 `pyaudio` 驱动，写入 `wave` 文件 `output.wav`。日志使用 `loguru`。

关键文件与位置
- `t1.py`：主程序，包含 `Worker`（音频采集逻辑）与 `ThreadExample`（GUI）。注意 `TARGET_DEVICE_NAME`、`RATE`、`CHUNK` 等常量。
- `README.md`：项目简介（简短）。
- `requirements.txt`：列出运行时依赖（`PySide6`, `PyAudio`, `loguru`）。
- `.github/workflows/windows-build.yml`：CI：在 `windows-latest` x86 上运行，使用 Python 3.12，包含 `pipwin` 针对 PyAudio 的 fallback 安装逻辑。

架构要点（大局观）
- 单窗口 GUI，UI 线程与工作线程分离：
  - `Worker` 是一个 `QObject`，在单独的 `QThread` 中运行（用 `moveToThread` 模式）。
  - 信号：`progress`（进度）与 `finished`（结束）用于主线程交互。
- 数据流：麦克风 -> PyAudio stream -> 写入 `wave.Wave_write` (`output.wav`)。
- 设备选择：`Worker.find_device()` 通过匹配 `TARGET_DEVICE_NAME` 寻找输入设备索引；当未找到时返回 `None` 并记录错误。

开发与构建流程（在此仓库可直接执行的步骤）
- 本地运行（推荐在 Windows 上测试 PyAudio）：
  ```bash
  python -m pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
  python t1.py
  ```
- 快速语法检查（CI 也会运行）：
  ```bash
  python -m py_compile t1.py
  ```
- 在 Windows CI 中：workflow 已设置为触发 `push` 到 `main` 与 `workflow_dispatch`（手动）。关键点：`actions/setup-python@v4` 使用 `architecture: 'x86'` 来安装 x86 Python。

项目约定与注意事项（只写可观察到的模式）
- QThread 使用约定：为 `Worker` 创建 `QThread`，`moveToThread`，连接 `t.started -> worker.do_work` 和 `worker.finished -> t.quit`。遵循这一模式以保证信号槽在正确线程执行。
- 录音参数在类常量中配置（`FORMAT`, `CHANNELS`, `RATE`, `CHUNK`, `RECORD_SECONDS`, `WAVE_OUTPUT_FILENAME`）。修改这些值时注意同步 `task()` 中的 `chunk_size` 计算。
- 日志：使用 `loguru`，偏好 `logger.info/debug/error` 而非 print，以便 CI/调试一致输出。

依赖与安装陷阱
- `PyAudio` 在 Windows 上经常需要预编译 wheel；CI 中已实现 fallback：若 `pip install -r requirements.txt` 失败，workflow 会安装 `pipwin` 并尝试 `pipwin install PyAudio`。
- 如果你需要替代方案，可考虑 `sounddevice` + `soundfile`，但这需要在代码中替换 `pyaudio` 的流式 API（非本说明所覆盖）。

调试提示（基于代码）
- 若找不到目标麦克风：检查 `Worker.TARGET_DEVICE_NAME` 的子串匹配；在不同系统/语言环境下设备名可能不同；建议在 debug 环境打印 `pa.get_device_info_by_index(i)` 列表以确认。
- PyAudio 读取时可能触发 `OSError`（缓冲/设备不匹配），在 `stream.read()` 周围添加异常处理以防止线程死锁并确保 `finished.emit()` 被调用。
- 在关闭线程时使用 `QThread.wait()`（如 `Worker.stop()` 中）确保线程已退出，避免资源泄漏。

PR 与自动化建议（供代理参考）
- 修改 GUI/线程逻辑时保留现有信号/连接模式；新增信号时同时更新 UI 端的 `connect` 逻辑。
- 若更新依赖版本，请同时更新 `requirements.txt` 与 CI 的安装逻辑；在升级主版本（如 PySide 7.x）前先在分支上验证。

变更示例（如何在 PR 中说明）
- 改动 `t1.py` 中 `RATE`：说明为何修改（例如支持 48k 录音），并在 PR 描述中指明是否影响 `chunk_size` 计算与延时表现。

如果有缺失或不准确的部分，请指出具体目标（例如：要把 `PyAudio` 替换为 `sounddevice`、或需支持 Linux/macOS 的 CI），我会基于仓库内容迭代本说明。
