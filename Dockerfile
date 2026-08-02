FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    poppler-utils \
    python3-tk \
    tk \
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY . .

EXPOSE 6080 5900

ENV DISPLAY=:99
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5
ENV HF_HUB_DISABLE_SYMLINKS_WARNING=1

COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
