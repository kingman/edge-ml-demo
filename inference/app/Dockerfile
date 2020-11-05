ARG PROJECT_ID
ARG BASE_IMAGE_ID
FROM gcr.io/${PROJECT_ID}/${BASE_IMAGE_ID}

WORKDIR /usr/src/app
COPY ./models /usr/src/app/models

ENV model="mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite"
ENV labels="coco_labels.txt"
