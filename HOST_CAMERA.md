# Docker 网页中的摄像头桥

Windows Docker Desktop 不会自动把摄像头传给 Linux 容器。项目通过宿主摄像头桥完成以下链路：

```text
Windows 摄像头
-> tools/host_camera_bridge.py
-> http://host.docker.internal:8091/frame.jpg
-> Docker 工作台
-> YOLO 与分拣状态机
```

## 启动顺序

在项目根目录打开一个 PowerShell 窗口：

```powershell
python tools/host_camera_bridge.py --camera-index 0
```

确认画面源已经就绪：

```powershell
Invoke-RestMethod http://127.0.0.1:8091/health
```

正常结果为：

```text
ready error
----- -----
True
```

再启动 Docker：

```powershell
docker compose up --build -d
```

然后打开：

```text
http://localhost:6080/vnc.html?autoconnect=1&resize=scale
```

进入工作台后点击“打开摄像头”，界面会直接切换到“宿主机摄像头桥”，不会弹出摄像头编号对话框。

如果有多台摄像头，可以修改 `--camera-index 0` 中的编号。

## 本机 Python 模式

不启动 Docker 时，仍可直接使用本机 Python：

```powershell
python -m simulator.lower_simulator
```

```powershell
python -m app.main
```

本机模式会在点击“打开摄像头”时弹出编号输入框。

## Docker 中选择视频

Docker 工作台中的“选择视频”不会打开 Linux 文件浏览器，而是显示：

- 项目自带的 `assets/assessment_demo.mp4`
- 项目自带的 `vedio/dep.mp4`
- `media` 文件夹中的视频

需要使用自己的视频时，把文件放进项目根目录的 `media` 文件夹，再点击“选择视频”。

也可以映射其他 Windows 文件夹：

```powershell
$env:HOST_MEDIA_DIR = "D:\Videos"
docker compose up --build -d
```

重新打开网页后，“选择视频”列表会包含该文件夹中的视频。

## 音频说明

noVNC 默认不转发 PyQt 容器内的音频。界面右上角的“背景音乐”勾选框会把播放状态写入网页，浏览器再直接播放 `assets/cycling_music.mp3`，因此无需 Linux 音频设备，整首歌会循环播放。

第一次勾选后，可能需要在 noVNC 画面中再点击一次，让浏览器授予播放权限。容器内 PyQt 的按键声仍不可用；需要演示按键声时使用本机 Python 模式。同一时间不要让本机应用和摄像头桥同时打开同一个摄像头。
