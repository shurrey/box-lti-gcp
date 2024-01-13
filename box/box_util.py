from boxsdk import JWTAuth, Client
from boxsdk.object.collaboration import CollaborationRole
import json

class box_util:

    def __init__(self, logger, box_user_id, box_root_folder):
        self.logger = logger
        self.service_client = None
        self.user_client = self.jwt(box_user_id)
        self.box_user_id = box_user_id
        self.box_root_folder = box_root_folder


    def jwt(self,user_id):

        self.logger.log_text("in jwt")
        auth = JWTAuth.from_settings_file('./jwt_settings.json')
        self.logger.log_text("got auth")
        self.service_client = Client(auth)

        self.logger.log_text(f"got client: {auth} ")

        user_to_impersonate = self.service_client.user(user_id=user_id)
        self.logger.log_text("got user")
        user_client = self.service_client.as_user(user_to_impersonate)
        self.logger.log_text("got user client")

        return user_client

    def me(self):
        return self.user_client.user().get()
    
    def create_course_folder(self,course_title, course_label):
        course_folder = self.service_client.folder(self.box_root_folder).create_subfolder(f"{course_title} - {course_label}")
        print(f'Created subfolder with ID {course_folder.id}')
        
        while True:
            folder = self.service_client.folder(folder_id=course_folder.id).get()

            if folder.name:
                return course_folder.id

    
    def create_course_group(self,course_title, course_label):
        created_group = self.service_client.create_group(f"{course_title} - {course_label}")
        print(f'Created group with ID {created_group.id}')
        return created_group.id

    def add_user_to_group(self,group_id, user_id):
        user = self.service_client.user(user_id)
        membership = self.service_client.group(group_id=group_id).add_member(user)
        print(f'Added {membership.user.name} to the {membership.group.name} group!')
        return membership.id

    def add_class_to_group(self,group_id, class_list, db):

        for student in class_list:
            user = db.get_user(student['user_id'])
            box_user = self.service_client.user(user["box_user_id"])
            membership = self.service_client.group(group_id=group_id).add_member(box_user)
            print(f'Added {membership.user.name} to the {membership.group.name} group!')
            student['box_group_membership_id'] = membership.id

        return class_list

    def remove_user_from_group(self, membership_id):
        self.service_client.group_membership(membership_id).delete() 
        print('The membership was deleted!')
    
    def create_collaborations(self,group_id, folder_id):
        self.logger.log_text(f"group_id {group_id} folder_id {folder_id}")
        group = self.service_client.group(group_id=group_id)
        self.logger.log_text(f"group {group} CollaborationRole.VIEWER {CollaborationRole.VIEWER}")
        collaboration = self.service_client.folder(folder_id=folder_id).collaborate(group, CollaborationRole.VIEWER)
        self.logger.log_text(f"collaboration id {collaboration.id}")
        
        #accepted_collab = self.service_client.collaboration(collab_id=collaboration.id).accept()