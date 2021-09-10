FROM python:3.7.9-slim-buster

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    libjpeg-dev \
    python3-opencv \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY ./module /usr/src/app
COPY ./templates /usr/src/app/templates
COPY ./static /usr/src/app/static
RUN python3 -m pip install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt
EXPOSE 8502

ENV PYTHONPATH="$PYTHONPATH:/usr/lib/python3/dist-packages:/usr/local/python3.7/dist-packages"
CMD python3 inference_web.py