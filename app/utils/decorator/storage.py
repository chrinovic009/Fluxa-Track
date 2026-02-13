import boto3
import os
from werkzeug.utils import secure_filename
import uuid

session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    endpoint_url=os.getenv("S3_ENDPOINT"),
    aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY")
)

def upload_to_s3(file, folder="uploads"):
    ext = file.filename.rsplit('.', 1)[-1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    key = f"{folder}/{unique_name}"
    s3.upload_fileobj(file, os.getenv("S3_BUCKET_NAME"), key)
    return f"{os.getenv('S3_ENDPOINT')}/{os.getenv('S3_BUCKET_NAME')}/{key}"

