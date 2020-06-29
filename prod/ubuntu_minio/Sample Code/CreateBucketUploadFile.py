# Import MinIO library.
from minio import Minio
from minio.error import (ResponseError, BucketAlreadyOwnedByYou,
                         BucketAlreadyExists)

# Initialize minioClient with an endpoint and access/secret keys.
minioClient = Minio('10.20.0.99:9000',
                    access_key='minioadmin',
                    secret_key='minioadmin',
                    secure=False)

# Make a bucket with the make_bucket API call.
try:
       minioClient.make_bucket("jfk1", location="us-east-1")
except BucketAlreadyOwnedByYou as err:
       pass
except BucketAlreadyExists as err:
       pass
except ResponseError as err:
       raise

# Put an object '104-10196-100270001.pdf' with contents from '104-10196-100270001.pdf'.
try:
       minioClient.fput_object('jfk1', '104-10196-100270001.pdf', '/home/phoenix/104-10196-100270001.pdf')
except ResponseError as err:
       print(err)


