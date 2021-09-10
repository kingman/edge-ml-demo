from google.cloud import storage
from iot_core import CloudIot
import logging
import os
import queue
import threading
import uuid

LOGFORMAT = "%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s"
logging.basicConfig(
    filename=f'{__name__}.log', level=logging.INFO, format=LOGFORMAT)

class DataCapture:
    def __init__(self, threshold, customExtractBytes, getMessageToUpload):
        try:
            self._threshold = float(threshold)
        except ValueError:
            raise ValueError('Provided value for threshold is not valid.')
        try:
            bucket_name = os.environ['GCS_UPLOAD_BUCKET']
        except KeyError:
            raise ValueError('Environment variable GCS_UPLOAD_BUCKET not set')
        if customExtractBytes is None:
            raise ValueError('Missing bytes extraction callback.')
        self._customExtractBytes = customExtractBytes
        if getMessageToUpload is None:
            raise ValueError('Missing create message callback.')
        self._getMessageToUpload = getMessageToUpload

        
        self._enabled = False
        self._queue = queue.Queue()
        storage_client = storage.Client()
        self._bucket = storage_client.bucket(bucket_name)
        self._iotCore = CloudIot()
        self._thread = None
    
    def toggleEnabled(self):
        self._enabled = not self._enabled
        self._startThread()
    
    def _startThread(self):
        if self._enabled and self._thread is None:
            self._thread = threading.Thread(target=self._store)
            self._thread.daemon = True
            self._thread.start()

    def isEnabled(self):
        return self._enabled
    
    def setThreshold(self, threshold):
        try:
            self._threshold = float(threshold)
        except ValueError:
            raise ValueError('Provided value for threshold is not valid.')
    
    def getThreshold(self):
        return self._threshold
    
    def isEligibleForCapture(self, inferenceScore):
        return self._enabled and inferenceScore > self._threshold
    
    def put(self, captureEntry):
        self._queue.put(captureEntry)
    
    def _store(self):
        while True:
            if self._enabled and not self._queue.empty():
                task = self._queue.get()
                file_name = f'{str(uuid.uuid4())}.jpg'
                dataToSend = self._customExtractBytes(task)
                self._bucket.blob(file_name).upload_from_string(dataToSend)
                fileUrl = self._bucket.blob(file_name).public_url
                message = self._getMessageToUpload(fileUrl)
                self._iotCore.publish_message(message)
                self._queue.task_done()        