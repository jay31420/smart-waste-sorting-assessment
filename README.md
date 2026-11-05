# 智能垃圾分拣上位机｜招新考核起始代码

这是一个无硬件也能完成闭环验收的招新项目。你需要在已有框架上完成视频/摄像头输入、YOLO 推理适配、二进制下位机通信、分拣状态机和 UI 优化。

系统链路如下：

```text
视频或摄像头 → Predict/best.pt → 状态机 → TCP 模拟下位机 → UI
                                      └→ Nano 上可替换为串口
```

仓库已经提供：

- 比赛 YOLO 权重 `Predict/best.pt`；
- 由真实比赛照片制作的 `assets/assessment_demo.mp4`；
- 原项目长视频 `vedio/dep.mp4`，用于视频跳转、暂停、重播和资源释放验收；
- 可构建的普通电脑 Docker 环境和 Jetson Nano/JetPack 4 镜像配置；
- 独立的 TCP 下位机模拟器；
- PyQt 界面骨架、后台线程、视频源和传输层；
- 协议文档与公开单元测试。

## 从这里开始

1. 阅读 [TASKS.md](TASKS.md) 和 [PROTOCOL.md](PROTOCOL.md)。
2. 搜索代码中的 `TODO`，依次完成协议、YOLO、状态机、`vedio` 视频模块和 UI 输入功能。
3. 先运行公开测试，再启动完整 Docker 演示。

```bash
python -m unittest discover -s tests -v
docker compose up --build
```

浏览器打开：

```text
http://localhost:6080/vnc.html?autoconnect=1&resize=scale
```

初始代码的公开测试会失败，这是考核设计的一部分。随着 TODO 完成，测试应逐步变绿。Docker 初始界面可以打开，但识别与通信闭环只有完成任务后才会正常工作。

停止容器：

```bash
docker compose down
```

## 本机运行（可选）

推荐优先使用 Docker。若需要本机调试，使用 Python 3.8：

```bash
python -m pip install -r requirements-local.txt
python -m simulator.lower_simulator
python -m app.main --auto-start
```

## Jetson Nano

`Dockerfile.nano` 面向经典 Jetson Nano 的 JetPack 4.x/L4T 32.x，基于 Ultralytics Jetson JetPack 4 镜像。只有在真实板卡上才能最终验证 GPU、摄像头和串口驱动：

```bash
cat /etc/nv_tegra_release
docker compose -f compose.yaml -f compose.nano.yaml up --build
```

使用实际摄像头或串口时，需要根据板卡设备增加 `/dev/video0` 或 `/dev/ttyUSB0` 映射。普通电脑完成考核时不要求 Nano 硬件。

## 约束

- 必须实际调用给定 YOLO 权重；不得用颜色阈值、标注文件或固定答案替代推理。
- 计数只能在下位机返回 `ACTION_DONE` 后更新。
- 不得把耗时推理放进 Qt 主线程。
- 不得删除或绕过公开测试；现场还会运行未公开边界测试。
- 请勿提交虚拟环境、Docker 镜像或额外的大体积模型。

最终提交要求、评分和验收场景见 [TASKS.md](TASKS.md)。

最终提交物为：3–4 分钟运行录屏、1 份设计说明与流程 PPT、可访问的 GitHub 源代码链接；提交后还会进行现场代码问辩。
