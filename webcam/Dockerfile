FROM arm64v8/debian
RUN apt update
RUN apt install curl ca-certificates zlib1g-dev libjpeg-dev python3-opencv -y

WORKDIR /usr/src/app
COPY ./module /usr/src/app

RUN pip3 install --no-cache-dir -r requirements.txt
ENV client_app="webcam_client_od.py"
ENV upload_target="https://us-central1-edgeml-demo.cloudfunctions.net/mledge-image-gateway-1/images/"
ENV upload_id="9999"
CMD ["python3","${client_app}", "-i", "1000", "--upload","${upload_target}", "--uploadid", "${upload_id}"]