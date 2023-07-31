from google.cloud import secretmanager
import google_crc32c

class secrets_util:

    def __init__(self, logger):
        self.logger = logger
        self.secrets_client = secretmanager.SecretManagerServiceClient()
        self.pub_key_name = f"projects/821305823385/secrets/box-lti-public-key/versions/1"
        self.prv_key_name = f"projects/821305823385/secrets/box-lti-private-key/versions/1"
        
    def get_key(self, public=False):
        
        if public:
            name = self.pub_key_name
        else:
            name = self.prv_key_name

        secret_obj = self.secrets_client.access_secret_version(request={"name": name})
        self.logger.log_text(f"secret_obj is {secret_obj}")

        # Verify payload checksum.
        crc32c = google_crc32c.Checksum()
        self.logger.log_text(f"crc32c is {crc32c}")
        crc32c.update(secret_obj.payload.data)
        if secret_obj.payload.data_crc32c != int(crc32c.hexdigest(), 16):
                self.logger.log_text("Data corruption detected.")
                return secret_obj

        secret = secret_obj.payload.data.decode("UTF-8")

        return secret