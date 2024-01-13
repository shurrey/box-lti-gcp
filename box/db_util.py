import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import datetime
import time

import box_util

class db_util:

    def __init__(self, logger):
        self.logger = logger
        self.client_id = ""
        self.deployment_id = ""

        self.base_doc = ""

        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()


    def set_params(self, client_id, deployment_id):
        self.client_id = client_id
        self.deployment_id = deployment_id

        self.base_doc = self.client_id + '|' + self.deployment_id

    def get_document(self,collection,document):
        doc_ref = self.db.collection(collection).document(document)

        doc = doc_ref.get()
        if doc.exists:
            self.logger.log_text(f"Document data for {collection}: {doc.to_dict()}")
            return doc.to_dict()
        else:
            self.logger.log_text(f"No such document for {collection}")
            return None
    
    def set_subcollection(self,collection,document,subcollection,subdocument,value):
        doc_ref = self.db.collection(collection).document(document)
        subdoc_ref = doc_ref.collection(subcollection).document(subdocument)

        subdoc_ref.set(value)
        
    def create_document(self, collection, document, cache_value):
        doc_ref = self.db.collection(collection).document(document)
        doc_ref.set(cache_value)

    def update_memberships(self, lms_course_id, lms_user_id, update):
        doc_ref = self.db.collection("courses").document(f"{self.base_doc}|{lms_course_id}").collection('memberships').document(lms_user_id)
        doc_ref.update(update)
        
    def delete_document(self,collection,document):
        doc_ref = self.db.collection(collection).document(document)
        doc_ref.delete()

    def get_config(self):

        config = {}
        cfg_dict = self.get_document('systems', self.base_doc)

        try:
            config['iss'] = cfg_dict['issuer']
            config['client_id'] = cfg_dict['client_id']
            config['deployment_id'] = cfg_dict['deployment_id']    
            config['auth_login_url'] = cfg_dict['auth_url']
            config['auth_token_url'] = cfg_dict['token_url']
            config['jwks_url'] = cfg_dict['jwks_url']
            if "auth_audience" in cfg_dict:
                config['auth_audience'] = cfg_dict['auth_audience']

            self.logger.log_text(f"config is {config}")

            return config
            
        except Exception as e:
            self.logger.log_text(f"LTIValidation->get_config: Error getting configuration - {e}", severity="ERROR")
            return None

    def get_cache_data(self,state):

        cache = {}
        
        state_str = str(state)
        
        cache_dict = self.get_document('cache', state_str)

        try:
            return cache_dict
        except Exception as e:
            self.logger.log_text(f"LTIValidation->get_cache: Error getting configuration - {e}", severity="ERROR")
            return None
        finally:
            self.delete_document('cache', state_str)
        
    
    def get_user(self, lms_user_id):

        user = {}
        
        usr_dict = self.get_document("users", self.base_doc + '|' + lms_user_id)

        try:
            user["lms_user_id"] = lms_user_id
            user["box_user_id"] = usr_dict['box_user_id']
            user["lms_system_roles"] = usr_dict['system_roles']

            print(f"user {user}")

            return user
        except Exception as e:
            self.logger.log_text(f"LTIValidation->get_user: Error getting user - {e}", severity="ERROR")
            return None
        
    
    def get_root_folder(self):

        cfg_dict = self.get_document('systems', self.base_doc)
        return cfg_dict['box_root_folder']
    
    def get_membership_count(self, lms_course_id):
        coll_ref = self.db.collection('courses').document(self.base_doc + '|' + lms_course_id).collection('memberships')
        return coll_ref.count().get()
        
    def get_course(self, lms_course_id):

        course = {}

        crs_dict = self.get_document('courses', self.base_doc + '|' + lms_course_id)

        self.logger.log_text(f"crs_dict {crs_dict}")

        try:
            course["lms_course_id"] = crs_dict['lms_course_id']
            course["box_course_folder_id"] = crs_dict['box_course_folder_id']
            course["box_group_id"] = crs_dict['box_group_id']
            course['system_id'] = crs_dict['system_id']
            course['nrps_url'] = crs_dict['nrps_url']
            course['groups_url'] = crs_dict['groups_url']
            course['groups_sets_url'] = crs_dict['groups_sets_url']
            course['lineitems_url'] = crs_dict['lineitems_url']
            if course['lms_course_id']:
                course['membership_count'] = self.get_membership_count(lms_course_id)
            

            print(f"course {course}")

            return course
        except Exception as e:
            self.logger.log_text(f"box->get_user: Error getting course - {e}", severity="ERROR")
            return None

    def create_course(self, launch_params, box_course_folder_id, box_group_id):

        lms_course_id = launch_params['https://purl.imsglobal.org/spec/lti/claim/context']['id']

        course = {
            "lms_course_id" : lms_course_id,
            "box_course_folder_id" : box_course_folder_id,
            "box_group_id" : box_group_id,
            "system_id" : launch_params['https://purl.imsglobal.org/spec/lti/claim/tool_platform']['guid'],
            'nrps_url' : launch_params['https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice']['context_memberships_url'],
            "groups_url" : launch_params['https://purl.imsglobal.org/spec/lti-gs/claim/groupsservice']['context_groups_url'],
            "groups_sets_url" : launch_params['https://purl.imsglobal.org/spec/lti-gs/claim/groupsservice']['context_group_sets_url'],
            "lineitems_url" : launch_params['https://purl.imsglobal.org/spec/lti-ags/claim/endpoint']['lineitems']
        }
        
        self.create_document('courses', self.base_doc + '|' + lms_course_id, course)

        course['membership_count'] = 0

        return course
    
    def get_membership(self, lms_course_id, lms_user_id):
        doc_ref = self.db.collection('courses').document(f"{self.base_doc}|{lms_course_id}").collection('memberships').document(lms_user_id)

        doc = doc_ref.get()
        if doc.exists:
            self.logger.log_text(f"Document data for memberships: {doc.to_dict()}")
            return doc.to_dict()
        else:
            self.logger.log_text(f"No such document for memberships")
            return None    
    
    def cache_token(self, access_token):
        exp_time = time.time() + int(access_token['expires_in'])

        expires_at = datetime.datetime.utcfromtimestamp(exp_time).isoformat()
        
        access_token['expires_at'] = expires_at

        self.create_document('auth_tokens', self.base_doc, access_token)

    def get_token(self):
        access_token = self.get_document('auth_tokens', self.base_doc)

        if access_token is None or access_token['expires_at'] <= datetime.datetime.utcfromtimestamp(time.time()).isoformat():
            self.logger.log_text(f"access token does not exist or is expired.")
            return None
        
        self.logger.log_text(f"access token is {access_token}")

        return access_token
    
    def save_class_list(self, lms_course_id, class_list):
        
        collection = 'courses'
        document = self.base_doc + '|' + lms_course_id
        subcollection = "memberships"

        for student in class_list["members"]:
            student_data = {}

            subdocument = student['user_id']

            student_data['status'] = student['status']
            student_data['roles'] = student['roles']
            student_data['box_collab_id'] = ""

            self.set_subcollection(collection, document, subcollection, subdocument, student_data)

