FROM python:3.7.9-slim-buster

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
    python3-pycoral \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY ./module /usr/src/app
RUN pip3 install -r requirements.txt
EXPOSE 8501

CMD python3 detection-service.py