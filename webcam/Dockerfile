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

RUN pip3 install --no-cache-dir -r requirements.txt
ENV client_app="webcam_client_od.py"
ENV upload_target="https://us-central1-edgeml-demo.cloudfunctions.net/mledge-image-gateway-1/images/"
ENV upload_id="9999"
ENV PYTHONPATH="$PYTHONPATH:/usr/lib/python3/dist-packages:/usr/local/python3.7/dist-packages"
CMD python3 ${client_app} -i 1000 --upload ${upload_target} --uploadid ${upload_id}