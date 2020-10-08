FROM python:3.8-slim-buster

ARG TARGETPLATFORM
ARG BUILDPLATFORM

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | tee /etc/apt/sources.list.d/coral-edgetpu.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -

RUN apt-get update \
    && apt install -y --no-install-recommends \
    libedgetpu1-std \
    python3-edgetpu \
    && rm -rf /var/lib/apt/lists/*

RUN if [ "$TARGETPLATFORM" = "linux/amd64" ]; then \
        pip install https://dl.google.com/coral/python/tflite_runtime-2.1.0.post1-cp38-cp38-linux_x86_64.whl; \
    elsif [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
        pip install https://dl.google.com/coral/python/tflite_runtime-2.1.0.post1-cp38-cp38-linux_aarch64.whl; \
    else \
        pip install https://dl.google.com/coral/python/tflite_runtime-2.1.0.post1-cp38-cp38-linux_armv7l.whl; \
    fi

WORKDIR /usr/src/app
COPY ./module /usr/src/app
COPY ./models /usr/src/app/models
RUN pip3 install -r requirements.txt
EXPOSE 5000

ENV label="coco_labels_5.txt"

CMD ["python3","coral-app.py", "--label", "${label}"]