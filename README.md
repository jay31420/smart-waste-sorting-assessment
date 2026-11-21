# 智能垃圾分拣上位机

本项目通过视频或摄像头读取图像，调用 `Predict/best.pt` 识别垃圾类别，再通过二进制协议向下位机发送分拣请求。普通电脑可使用 TCP 模拟下位机完成闭环演示；Jetson Nano 可切换到串口。

```text
视频/摄像头 → OpenCV 逐帧读取 → YOLO → 分拣状态机 → TCP/串口下位机
                                      └→ PyQt 状态、检测结果与通信日志
```

## 功能

- OpenCV 视频源支持逐帧读取、暂停、重播、进度显示和跳转；界面可导入视频或选择摄像头。
- YOLO 适配器加载指定权重，过滤低置信度结果、映射四类垃圾并按置信度排序。
- 通信层支持 TCP 与串口，解析器处理分片、粘连、噪声、校验错误和重新同步。
- 状态机要求连续稳定识别后发送指令，按原序号重试；只在匹配的 `ACTION_DONE` 到达后更新数量，并等待目标离开后重新布防。
- PyQt 界面展示检测画面、分类结果、计数、满载状态、连接状态、FPS 和 TX/RX 帧日志。
- 开场页以动态郊野分拣场景呈现项目；点击电脑进入工作台，点击顶部云朵控件返回。可分别关闭按键声和自然轻音乐；偏好会保存在本机设置中。
- 视频播完后可从头重播；每次新一轮会清空连续帧候选状态，但保留已完成的分拣计数。关闭窗口时会等待后台识别线程完成清理，再退出。

通信协议细节见 [PROTOCOL.md](PROTOCOL.md)。

## 测试

在仓库根目录运行：

```bash
python -m unittest discover -s tests -v
```

测试覆盖协议编解码、控制器状态流转、YOLO 结果适配和两段视频的读取、跳转与重播。

## Docker 演示

需要安装 Docker Engine 或 Docker Desktop：

```bash
docker compose up --build
```

浏览器打开：

```text
http://localhost:6080/vnc.html?autoconnect=1&resize=scale
```

结束后停止容器：

```bash
docker compose down
```

Compose 默认使用 `assets/assessment_demo.mp4` 和 `Predict/best.pt`。摄像头输入需要把设备映射进容器；普通电脑演示不要求 Nano 硬件。

## 本机运行

建议使用 Python 3.8，并安装 `requirements-local.txt`。分别在两个终端启动模拟下位机和上位机：

```bash
python -m pip install -r requirements-local.txt
python -m simulator.lower_simulator
```

```bash
python -m app.main --auto-start
```

如果要验证声音资源，可以在本地重新生成：

```bash
python tools/generate_scene_audio.py
```

声音依赖系统可用的音频输出设备；无输出设备时，两个声音开关会禁用，识别和分拣功能不受影响。

## 设计说明与演示材料

- 可编辑设计说明与流程幻灯片：`deliverables/smart-waste-sorting-defense-final.pptx`。
- 展示/打印版：`deliverables/smart-waste-sorting-defense-final.pdf`。PDF 按幻灯片页面渲染，可编辑内容以 PPTX 为准。

## Docker 摄像头与宿主媒体

宿主摄像头桥用于把 Windows 摄像头画面送入 Docker 工作台。启动方式、`media` 文件夹和 `HOST_MEDIA_DIR` 配置见 [HOST_CAMERA.md](HOST_CAMERA.md)。

## Jetson Nano

`Dockerfile.nano` 面向 JetPack 4.x/L4T 32.x。Nano 上的 GPU、摄像头和串口驱动需在实际板卡验证：

```bash
cat /etc/nv_tegra_release
docker compose -f compose.yaml -f compose.nano.yaml up --build
```

使用板载摄像头或串口时，按实际设备增加 `/dev/video0` 或 `/dev/ttyUSB0` 映射。

