from boxsdk import OAuth2, Client
import json

class box_util:

    def __init__(self, logger):
        self.logger = logger
        self.client = None

    def getIdAndSecret(self):

        f = open('oauth_settings.json')
        box_cfg = json.load(f)

        client_id = box_cfg['client_id']
        client_secret = box_cfg['client_secret']

        return client_id, client_secret



    def oauth2(self, code):

        client_id, client_secret = self.getIdAndSecret()
        self.logger.log_text(f"get OAuth2 id {client_id} secret {client_secret}")
        
        oauth = OAuth2(
            client_id=client_id,
            client_secret=client_secret
        )
        self.logger.log_text(f"oauth set")

        access_token, refresh_token = oauth.authenticate(code)
        self.client = Client(oauth)

        self.logger.log_text(f"access_token {access_token} refresh_token {refresh_token}")

        return self.client.user().get()