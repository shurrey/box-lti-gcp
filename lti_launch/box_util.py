from boxsdk import OAuth2, JWTAuth, Client
import json

class box_util:

    def __init__(self, logger):
        self.logger = logger
        self.user_client = None

    def getIdAndSecret(self):

        f = open('oauth_settings.json')
        box_cfg = json.load(f)

        client_id = box_cfg['client_id']
        client_secret = box_cfg['client_secret']

        return client_id, client_secret



    def oauth2(self):

        client_id, client_secret = self.getIdAndSecret()
        self.logger.log_text(f"get OAuth2 id {client_id} secret {client_secret}")
        
        oauth = OAuth2(
            client_id=client_id,
            client_secret=client_secret
        )
        self.logger.log_text(f"oauth set")

        auth_url, csrf_token = oauth.get_authorization_url('https://us-central1-box-lti-392219.cloudfunctions.net/auth_redirect')

        self.logger.log_text(f"auth_url {auth_url} csrf_token {csrf_token}")

        return auth_url, csrf_token

    def jwt(self,user_id):

        self.logger.log_text("in jwt")
        auth = JWTAuth.from_settings_file('./jwt_settings.json')
        self.logger.log_text("got auth")
        client = Client(auth)

        self.logger.log_text(f"got client: {auth} ")

        user_to_impersonate = client.user(user_id=user_id)
        self.logger.log_text("got user")
        self.user_client = client.as_user(user_to_impersonate)
        self.logger.log_text("got user client")

    def me(self):
        return self.user_client.user().get()