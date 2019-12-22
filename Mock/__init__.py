import logging
import json
import os
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED as deflated
from datetime import datetime, timezone
import azure.functions as func
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

def main(req: func.HttpRequest) -> func.HttpResponse:

    logging.info('Generating request dump')

    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = "uploads"
    file_name = datetime.now(timezone.utc).isoformat() + ".zip"

    request = {
       "url": req.url,
       "method": req.method,
       "headers": req.headers.__http_headers__
    }

    mem_zip = BytesIO()

    with ZipFile(mem_zip, mode="w", compression=deflated) as zf:
        zf.writestr("request.txt", json.dumps(request))
        if req.files.__len__() > 0:
            logging.info('Attaching request files')
            for file in req.files:
                file_data = req.files[file].stream.read()
                zf.writestr(file, file_data)

    data = mem_zip.getvalue()

    logging.info('Accessing blob container')
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    try:
        container_client = blob_service_client.create_container(container_name)
    except ResourceExistsError:        
        pass
    
    logging.info('Writing to blob storage')
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    blob_client.upload_blob(data)

    #TODO: response rules

    return func.HttpResponse("OK")
