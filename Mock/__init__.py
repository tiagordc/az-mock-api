from logging import info as log
from json import dumps as stringify
from os import getenv
from datetime import datetime, timezone
import azure.functions as func
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

def main(req: func.HttpRequest) -> func.HttpResponse:

    log('Generating request dump')

    connection_string = getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = "uploads"
    file_name = datetime.now(timezone.utc).isoformat()

    request = {
       "url": req.url,
       "method": req.method,
       "headers": req.headers.__http_headers__
    }

    if hasattr(req, "form") and len(req.form) > 0:
        request["form"] = req.form

    data = None

    if hasattr(req, "files") and len(req.files) > 0:

        from io import BytesIO
        from zipfile import ZipFile, ZIP_DEFLATED as deflated

        log('Creating zip file')
        mem_zip = BytesIO()

        with ZipFile(mem_zip, mode="w", compression=deflated) as zf:
            zf.writestr("request.txt", stringify(request))
            for file in req.files:
                file_data = req.files[file].stream.read()
                zf.writestr(file, file_data)

        data = mem_zip.getvalue()
        file_name += ".zip"

    else:
        data = stringify(request).encode('utf-8')
        file_name += ".txt"

    log('Accessing blob container')
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    try:
        container_client = blob_service_client.create_container(container_name)
    except ResourceExistsError:        
        pass
    
    log('Writing to blob storage')
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    blob_client.upload_blob(data)

    #TODO: response rules

    return func.HttpResponse("OK")
