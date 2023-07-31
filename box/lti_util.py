import base64
import json
import jwt
from jwcrypto import jwk
from google.cloud import logging
import os
from pprint import pformat
from urllib import parse as urlparse
import urllib3
import secrets_util
import uuid
import time
import requests

class lti_util:

    def __init__(self, logger, client_id, token_url, nrps_url):
        self.logger = logger
        self.client_id = client_id
        self.token_url = token_url
        self.nrps_url = nrps_url

        self.sec_svc = secrets_util.secrets_util(self.logger)

        self.TOOL_ISSUER = "https://box.com"
        self.NRPS_CONTENT_TYPE = 'application/vnd.ims.lti-nrps.v2.membershipcontainer+json'
        self.NRPS_SCOPE = 'https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly'

    def get_kid(self):

        public_key=self.sec_svc.get_key(True)

        key = jwk.JWK.from_pem(public_key.encode('utf-8'))
        public_jwk = json.loads(key.export_public())
        
        return public_jwk['kid']


    def build_jwt_for_token(self):

        private_key=self.sec_svc.get_key()

        nonce = uuid.uuid4().hex

        now = int(time.time())
        exp = now + 300

        jwt_body = {
            "iss" : self.TOOL_ISSUER,
            "sub": self.client_id,
            "aud": [ self.token_url ],
            "jti": nonce,
            "exp": exp,
            "iat": now
        } 

        headers = {
            "kid": self.get_kid()
        }

        self.logger.log_text(f"headers are {headers}")

        encoded = jwt.encode(jwt_body, private_key, algorithm="RS256", headers=headers)
        print(encoded)

        return encoded
    
    def get_lti_token(self):

        jwt_token = self.build_jwt_for_token()

        headers = {
            'Content-Type' : 'application/x-www-form-urlencoded'
        }

        params = {
            'grant_type' : 'client_credentials',
            'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            'client_assertion' : jwt_token,
            'scope' : self.NRPS_SCOPE
        }

        body = urlparse.quote(json.dumps(params, ensure_ascii=False).encode('utf-8'))

        self.logger.log_text(f"headers {headers}")
        self.logger.log_text(f"params {params}")
        self.logger.log_text(f"body {body}")

        res = requests.post(self.token_url, data=params, headers=headers)

        self.logger.log_text(f"token res is {res.text}")

        return res.json()


    
    def get_nrps_data(self,access_token):
        
        headers = {
            'Authorization' : 'Bearer ' + access_token,
            'Accepts' : self.NRPS_CONTENT_TYPE
        }

        res = requests.get(self.nrps_url, headers=headers)

        self.logger.log_text(f"nrps res is {res.text}")

        return res.json()