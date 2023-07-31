from boxsdk import JWTAuth, Client
import json

class box_util:

    def __init__(self, logger, box_user_id, box_root_folder):
        self.logger = logger
        self.user_client = self.jwt(box_user_id)
        self.box_user_id = box_user_id
        self.box_root_folder = box_root_folder


    def jwt(self,user_id):

        self.logger.log_text("in jwt")
        auth = JWTAuth.from_settings_file('./jwt_settings.json')
        self.logger.log_text("got auth")
        client = Client(auth)

        self.logger.log_text(f"got client: {auth} ")

        user_to_impersonate = client.user(user_id=user_id)
        self.logger.log_text("got user")
        user_client = client.as_user(user_to_impersonate)
        self.logger.log_text("got user client")

        return user_client

    def me(self):
        return self.user_client.user().get()
    
    def create_course_folder(self,course_title, course_label):
        course_folder = self.user_client.folder(self.box_root_folder).create_subfolder(f"{course_title} - {course_label}")
        print(f'Created subfolder with ID {course_folder.id}')
        return course_folder.id