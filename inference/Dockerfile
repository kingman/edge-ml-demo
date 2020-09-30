FROM arm64v8/debian

RUN apt update
RUN apt install curl gnupg ca-certificates zlib1g-dev libjpeg-dev -y

RUN echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | tee /etc/apt/sources.list.d/coral-edgetpu.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -

RUN apt update
RUN apt install libedgetpu1-std python3 python3-pip python3-edgetpu  -y

RUN pip3 install https://dl.google.com/coral/python/tflite_runtime-2.1.0.post1-cp37-cp37m-linux_aarch64.whl

WORKDIR /usr/src/app
COPY ./module /usr/src/app
COPY ./models /usr/src/app/models
RUN pip3 install -r requirements.txt
EXPOSE 5000

ENV label="coco_labels_5.txt"

CMD ["python3","coral-app.py", "--label", "$label"]