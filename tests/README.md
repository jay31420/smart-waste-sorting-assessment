# 公开测试说明

这些测试用于帮助你逐步完成任务，初始状态失败是正常现象。

```bash
python -m unittest discover -s tests -v
```

- `test_protocol.py`：半包、粘包、噪声和错误校验；
- `test_controller.py`：稳定识别、完整分拣周期、重试与满载；
- `test_cv_detector.py`：演示视频、YOLO API 适配和未知类别。

公开测试只是最低要求；验收还会覆盖更多边界条件。
