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

    def get_cache_data(self, csrf_token):
        return self.get_document('cache', csrf_token)
        
    def add_user(self, user, launch_data):
        doc_name = f"{launch_data['aud']}|{launch_data['https://purl.imsglobal.org/spec/lti/claim/deployment_id']}|{launch_data['sub']}"

        system_roles = []
        for role in launch_data['https://purl.imsglobal.org/spec/lti/claim/roles']:
            if role.find("/system/") != -1 or role.find("/institution/") != -1:
                system_roles.append(role)
        
        user_object = {
            "box_user_id" : user.id,
            "lms_user_id" : launch_data['sub'],
            "system_id" : launch_data['https://purl.imsglobal.org/spec/lti/claim/tool_platform']['guid'],
            "system_roles" : system_roles
        }
        
        self.create_document('users', doc_name, user_object)
