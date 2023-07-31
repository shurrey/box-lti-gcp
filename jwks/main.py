import functions_framework
import base64
import json
from google.cloud import logging
from google.cloud import secretmanager
import google_crc32c
import os
from pprint import pformat

from flask import request
from jwcrypto import jwk

# Configure Logger
logging_client = logging.Client()
logger = logging_client.logger('lti_launch')

def getJwks():
        client = secretmanager.SecretManagerServiceClient()

        # Build the resource name of the secret version.
        name = f"projects/821305823385/secrets/box-lti-public-key/versions/1"
        logger.log_text(f"name is {name}")

        # Access the secret version.
        secret = client.access_secret_version(request={"name": name})
        logger.log_text(f"secret is {secret}")

        # Verify payload checksum.
        crc32c = google_crc32c.Checksum()
        logger.log_text(f"crc32c is {crc32c}")
        crc32c.update(secret.payload.data)
        if secret.payload.data_crc32c != int(crc32c.hexdigest(), 16):
                print("Data corruption detected.")
                return secret

        public_pem = secret.payload.data.decode("UTF-8")

        key = jwk.JWK.from_pem(public_pem.encode('utf-8'))
        public_jwk = json.loads(key.export_public())
        public_jwk['alg'] = 'RS256'
        public_jwk['use'] = 'sig'

        logger.log_text(f"key {key} public_jwk {public_jwk}")

        jwks = {
                "keys" : [
                        public_jwk
                ]
        }

        headers = {"Content-Type": "application/json"}


        return (json.dumps(jwks), 200, headers)

@functions_framework.http
def jwks(request):
        
        return getJwks()