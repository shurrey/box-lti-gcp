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
import lti_util



# Configure Logger
logging_client = logging.Client()
logger = logging_client.logger('lti_launch')

db = db_util.db_util(logger)

# Configure LTI (TODO: move this to database)
course = {}
config = {}
launch_data = {}
user = {}


def get_course_role(launch_params):
    return 'http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor' in launch_params['https://purl.imsglobal.org/spec/lti/claim/roles']

@functions_framework.http
def box(request):

    args = request.args
    
    launch_id = args.get('launch_id')

    launch_params = db.get_cache_data(launch_id)

    logger.log_text(f"launch params {launch_params}")

    client_id = launch_params['aud']
    deployment_id = launch_params['https://purl.imsglobal.org/spec/lti/claim/deployment_id']
    lms_user_id = launch_params['sub']
    lms_course_id = launch_params['https://purl.imsglobal.org/spec/lti/claim/context']['id']

    db.set_params(client_id, deployment_id)

    isInstructor = get_course_role(launch_params)

    config = db.get_config()
    
    user = db.get_user(lms_user_id)

    box_root_folder = db.get_root_folder()
    box = box_util.box_util(logger, user["box_user_id"],box_root_folder)

    
    course = db.get_course(lms_course_id)

    if course is None:
        # Create course folder and object

        if isInstructor:
            course_title = launch_params['https://purl.imsglobal.org/spec/lti/claim/context']['title']
            course_label = launch_params['https://purl.imsglobal.org/spec/lti/claim/context']['label']
            box_course_folder_id = box.create_course_folder(course_title, course_label)

            course = db.create_course(launch_params, box_course_folder_id)
        else:
            return "Course not found, please contact the course instructor.", 404
    
    if isInstructor:
        lti = lti_util.lti_util(logger, client_id, config['auth_token_url'], course['nrps_url'])

        access_token = db.get_token()

        if access_token is None:
        
            access_token = lti.get_lti_token()

            if access_token is None:
                return ("Error getting access token", 401)
            else:
                db.cache_token(access_token)

        nprs_data = lti.get_nrps_data(access_token["access_token"])

        db.save_class_list(lms_course_id, nprs_data['members'])

    return (f"user {user}\ncourse {course}")