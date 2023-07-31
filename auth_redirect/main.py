import functions_framework
from google.cloud import logging

import base64
import json
import os
from pprint import pformat
from urllib import parse as urlparse
import uuid

from flask import redirect, request

import box_util
import db_util

# Configure Logger
logging_client = logging.Client()
logger = logging_client.logger('lti_launch')

db = db_util.db_util(logger)

config = {}
launch_data = {}
user = {}


@functions_framework.http
def auth_redirect(request):

    args = request.args
    
    csrf_token = args.get('state')
    auth_code = args.get('code')

    launch_params = db.get_cache_data(csrf_token)

    logger.log_text(f"launch params {launch_params}")

    box = box_util.box_util(logger)

    user = box.oauth2(auth_code)

    db.add_user(user,launch_params)

    launch_id =launch_params['nonce']
    nonce = uuid.uuid4().hex
    
    db.create_document('cache', launch_id, launch_params)
    
    return redirect (f"/box?launch_id={launch_id}&nonce={nonce}")