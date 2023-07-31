import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

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
        
    def create_document(self, collection, document, cache_value):
        doc_ref = self.db.collection(collection).document(document)
        doc_ref.set(cache_value)
        
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
            cache["iss"] = cache_dict['iss']
            cache["lti_deployment_id"] = cache_dict['lti_deployment_id']
            cache["client_id"] = cache_dict['client_id']
            cache["login_hint"] = cache_dict["login_hint"]
            cache["target_link_uri"] = cache_dict["target_link_uri"]
            cache["lti_message_hint"] = cache_dict["lti_message_hint"]
            cache["lti_storage_target"] = cache_dict["lti_storage_target"]

            print(f"cache {cache}")

            return cache
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
        