# Reproducible PC/amd64 assessment image with CPU YOLO inference.
ARG YOLO_BASE_IMAGE=docker.m.daocloud.io/ultralytics/ultralytics:8.4.201-cpu
FROM ${YOLO_BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    DISPLAY=:99 \
    QT_X11_NO_MITSHM=1 \
    YOLO_CONFIG_DIR=/tmp/Ultralytics

RUN for source in /etc/apt/sources.list /etc/apt/sources.list.d/*; do \
      [ -f "$source" ] || continue; \
      sed -i \
        -e 's|http://deb.debian.org/debian-security|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' \
        -e 's|http://deb.debian.org/debian|https://mirrors.tuna.tsinghua.edu.cn/debian|g' \
        "$source"; \
    done \
    && apt-get -o Acquire::Retries=10 -o Acquire::http::Timeout=30 update \
    && apt-get -o Acquire::Retries=10 -o Acquire::http::Timeout=30 install -y --fix-missing --no-install-recommends \
    fonts-wqy-zenhei \
    libegl1 \
    libgl1 \
    libglib2.0-0 \
    libxkbcommon-x11-0 \
    novnc \
    openbox \
    tigervnc-standalone-server \
    websockify \
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
COPY Predict /workspace/Predict
COPY assets /workspace/assets
COPY vedio /workspace/vedio
COPY simulator /workspace/simulator
COPY docker /workspace/docker
COPY app /workspace/app
RUN chmod +x /workspace/docker/start-ui.sh

EXPOSE 6080 5900
CMD ["/workspace/docker/start-ui.sh"]
