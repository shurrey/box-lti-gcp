import base64
import json
import jwt
from google.cloud import logging
import os
from pprint import pformat
from urllib import parse as urlparse
import urllib3
import secrets
import uuid
import time
import requests

class lti_util:

    def __init__(self, logger, client_id, jwks_url):
        self.logger = logger
        self.client_id = client_id
        self.jwks_url = jwks_url

        self.http = urllib3.PoolManager()

        self.NRPS_CONTENT_TYPE = 'application/vnd.ims.lti-nrps.v2.membershipcontainer+json'
        self.NRPS_SCOPE = 'https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly'

    def decode_jwt_parts(self, part):
        self.logger.log_text(f"LTIValidation->decode_jwt_parts: part: {part}")
        s = str(part).strip()
        self.logger.log_text(f"LTIValidation->decode_jwt_parts: s: {s}")

        remainder = len(part) % 4
        if remainder > 0:
            padlen = 4 - remainder
            part = part + ('=' * padlen)
        if hasattr(str, 'maketrans'):
            tmp = part.translate(str.maketrans('-_', '+/'))
            return base64.b64decode(tmp).decode("utf-8")
        else:
            tmp = str(part).translate(string.maketrans('-_', '+/'))
            return base64.b64decode(tmp)

        
    def process_launch(self, id_token):
        self.logger.log_text(f"LTIValidation->process_launch: id_token: {id_token}")

        jwt_parts = id_token.split(".")
        self.logger.log_text(f"LTIValidation->process_launch: jwt_parts: {jwt_parts}")
        self.logger.log_text(f"LTIValidation->process_launch: jwt_parts: header {jwt_parts[0]}")
        self.logger.log_text(f"LTIValidation->process_launch: jwt_parts: body {jwt_parts[1]}")
        self.logger.log_text(f"LTIValidation->process_launch: jwt_parts: {jwt_parts[2]}")

        jwt_header = json.loads(self.decode_jwt_parts(jwt_parts[0]))
        self.logger.log_text(f"LTIValidation->process_launch: jwt_header: " + pformat(jwt_header))

        jwt_body = json.loads(self.decode_jwt_parts(jwt_parts[1]))
        self.logger.log_text(f"LTIValidation->process_launch: jwt_body: " + pformat(jwt_body))

        aud = ""
        if isinstance(jwt_body['aud'], list):
            aud = jwt_body['aud'][0]
        else:
            aud = jwt_body['aud']

        self.logger.log_text(f"LTIValidation->process_launch: aud: {aud}")
        self.logger.log_text(f"LTIValidation->process_launch: client_id: {self.client_id}")
        
        if aud != self.client_id:
            self.logger.log_text(f"LTIValidation->process_launch: Invalid client Id {aud} {self.client_id}", severity="ERROR")
            return 'Invalid client_id', 401
            

        self.logger.log_text(f"LTIValidation->process_launch: get public key: {jwt_header['kid']}")
        
        try:
            jwks_client = jwt.PyJWKClient(self.jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(id_token)
            data = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                options={"verify_exp": False},
            )
            self.logger.log_text(f"LTIValidation->process_launch: post_validation_data: {data}")

            return data

        except Exception as e:
            self.logger.log_text(f"LTIValidation->process_launch: Exception: {e}", severity="ERROR")
            return f"LTIValidation->process_launch: Exception: {e}", 500
    
    def get_lms_data(self,launch_data):

        lms_data = {
            "deployment_id" : launch_data["https://purl.imsglobal.org/spec/lti/claim/deployment_id"],
            "system_guid" : launch_data["https://purl.imsglobal.org/spec/lti/claim/tool_platform"]["guid"],
            "client_id" : launch_data["aud"],
            "issuer" : launch_data["iss"],
            "lms" : launch_data["https://purl.imsglobal.org/spec/lti/claim/tool_platform"]["name"],
            "url" : launch_data["https://purl.imsglobal.org/spec/lti/claim/tool_platform"]["url"],
            "contact_email" : launch_data["https://purl.imsglobal.org/spec/lti/claim/tool_platform"]["contact_email"],
            "version" : launch_data["https://purl.imsglobal.org/spec/lti/claim/tool_platform"]["version"],
            "user_id" : launch_data["sub"],
            "user_role" : [launch_data["https://purl.imsglobal.org/spec/lti/claim/roles"]],
            "message_type" : launch_data["https://purl.imsglobal.org/spec/lti/claim/message_type"]
        }

        return lms_data
    
    def build_jwt_for_token(self, token_url):
        sec_svc = secrets.secrets(self.logger)

        private_key=sec_svc.get_key()

        nonce = uuid.uuid4().hex

        now = int(time.time())
        exp = now + 300

        jwt_body = {
            "iss" : "box.com",
            "sub": self.client_id,
            "aud": [ token_url ],
            "jti": nonce,
            "exp": exp,
            "iat": now
        } 

        encoded = jwt.encode(jwt_body, private_key, algorithm="RS256")
        print(encoded)

        return encoded
    
    def get_lti_token(self, token_url):

        jwt_token = self.build_jwt_for_token(token_url)

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

        res = requests.post(token_url, data=body, headers=headers)

        self.logger.log_text(f"res is {res.text}")

        return res


    
    def get_nrps_data(self,nrps_url,access_token):
        
        headers = {
            'Authorization' : 'Bearer ' + access_token,
            'Accepts' : self.NRPS_CONTENT_TYPE
        }

        response = requests.get(nrps_url, headers=headers)