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

    #connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    connection_string = "DefaultEndpointsProtocol=https;AccountName=storageaccountmocki9aca;AccountKey=8frtmVQ5QuGt7JoH3Uf5PIBAYDx1biKX7Aik5LtmmcX7bOeAsqKSPAt6Bl3k5CALglrp2VRw1SsGy5wV9BO02g==;EndpointSuffix=core.windows.net"
    container_name = "uploads"
    file_name = datetime.now(timezone.utc).isoformat() + ".zip"

    request = {
       "url": req.url,
       "method": req.method,
       "headers": req.headers.__http_headers__
    }

    if hasattr(req, "form") and len(req.form) > 0:
        request["form"] = req.form

    mem_zip = BytesIO()

    with ZipFile(mem_zip, mode="w", compression=deflated) as zf:
        zf.writestr("request.txt", json.dumps(request))
        if hasattr(req, "files") and len(req.files) > 0:
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
