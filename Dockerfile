# Reproducible PC/amd64 assessment image with CPU YOLO inference.
FROM ultralytics/ultralytics:8.4.201-cpu

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    DISPLAY=:99 \
    QT_X11_NO_MITSHM=1 \
    YOLO_CONFIG_DIR=/tmp/Ultralytics

RUN apt-get -o Acquire::Retries=10 -o Acquire::http::Timeout=30 update \
    && apt-get -o Acquire::Retries=10 -o Acquire::http::Timeout=30 install -y --fix-missing --no-install-recommends \
    fonts-wqy-zenhei \
    libegl1 \
    libgl1 \
    libglib2.0-0 \
    libxkbcommon-x11-0 \
    novnc \
    openbox \
    websockify \
    x11vnc \
    xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir PyQt5==5.15.11 pyserial==3.5

RUN apt-get -o Acquire::Retries=10 -o Acquire::http::Timeout=30 update \
    && apt-get -o Acquire::Retries=10 -o Acquire::http::Timeout=30 install -y --no-install-recommends \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY . /workspace
RUN chmod +x /workspace/docker/start-ui.sh

EXPOSE 6080 5900
CMD ["/workspace/docker/start-ui.sh"]
