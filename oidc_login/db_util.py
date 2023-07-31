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
        self.base_doc = client_id + '|' + deployment_id
    
    def get_document(self,collection, document):
        doc_ref = self.db.collection(collection).document(document)

        doc = doc_ref.get()
        if doc.exists:
            self.logger.log_text(f"Document data for {collection}: {doc.to_dict()}")
            return doc.to_dict()
        else:
            self.logger.log_text(f"No such document for {collection}")
            return None

    def get_config(self):
            
            config = {}

            ddoc = self.get_document('systems', self.base_doc)

            try:
                config['iss'] = ddoc['issuer']
                config['client_id'] = ddoc['client_id']
                config['deployment_id'] = ddoc['deployment_id']    
                config['auth_login_url'] = ddoc['auth_url']
                config['auth_token_url'] = ddoc['token_url']
                config['jwks_url'] = ddoc['jwks_url']
                if "auth_audience" in ddoc:
                    config['auth_audience'] = ddoc['auth_audience']

                self.logger.log_text(f"config is {config}")

                return config
            except Exception as e:
                self.logger.log_text(f"oidc_login->get_config: Error getting configuration - {e}", severity="ERROR")
                return None
    
    def cache(self,state, cache_value):
        state_str = str(state)
        doc_ref = self.db.collection("cache").document(state_str)
        doc_ref.set(cache_value)