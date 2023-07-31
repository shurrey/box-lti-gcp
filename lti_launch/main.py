import functions_framework
from google.cloud import logging

import base64
import json
import os
from pprint import pformat
from urllib import parse as urlparse
import uuid

from flask import redirect


import box_util
import db_util
import lti_util

# Configure Logger
logging_client = logging.Client()
logger = logging_client.logger('lti_launch')

db = db_util.db_util(logger)

config = {}
cache = {}
user = {}
    
@functions_framework.http
def lti_launch(request):
    
    try:
        
        launch_params = request.form
        
        logger.log_text(f"launch params {launch_params}")

        id_token = launch_params['id_token']
        logger.log_text(f"id_token {id_token}")
        state = launch_params['state']
        logger.log_text(f"state {state}")
        
        cache = db.get_cache_data(state)
        logger.log_text(f"cache {cache}")

        if not cache:
            retval='Invalid state parameter. You no hax0r!'
            logger.log_text(f"Error: {retval}")
            return retval, 401
        
        db.set_params(cache["client_id"], cache["lti_deployment_id"])

        config = db.get_config()

        if not config:
            retval='Invalid configuration. You no hax0r!'
            logger.log_text(f"Error: {retval}")
            return retval, 401

        logger.log_text(f"client ID {config['client_id']} jwks_url {config['jwks_url']}")

        lti = lti_util.lti_util(logger,config['client_id'],config['jwks_url'])
        
        logger.log_text("get json")
        launch_data = lti.process_launch(id_token)
        logger.log_text(f"launch_data {launch_data}")

        lms_data = lti.get_lms_data(launch_data)
        logger.log_text(f"lms_data {lms_data}")

        user = db.get_user(launch_data['sub'])

        box = box_util.box_util(logger)

        logger.log_text(f"if not user")

        if user is None:
            logger.log_text(f"call oauth2")
            auth_url, csrf_token = box.oauth2()

            logger.log_text(f"auth_url {auth_url} csrf_token {csrf_token}")

            db.create_document('cache', csrf_token, launch_data)

            return redirect(auth_url)
        
        launch_id =launch_data['nonce']
        nonce = uuid.uuid4().hex
        
        db.create_document('cache', launch_id, launch_data)
        
        return redirect (f"/box?launch_id={launch_id}&nonce={nonce}")

    except Exception as e:
        logger.log_text(f"LTIValidation: Error validating lti launch - {e}", severity="ERROR")
        return str(e), 500
