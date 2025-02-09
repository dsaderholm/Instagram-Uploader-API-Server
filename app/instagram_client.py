from instagrapi import Client
import os
import json

class InstagramClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.client = None
        self._login()

    def _login(self):
        self.client = Client()
        # Store sessions in /tmp since we know it's writable
        session_file = f'/tmp/instagram_session_{self.username}.json'
        
        if os.path.exists(session_file):
            try:
                self.client.load_settings(session_file)
                self.client.login(self.username, self.password, relogin=True)
                return
            except Exception:
                pass

        self.client.login(self.username, self.password)
        self.client.dump_settings(session_file)

    def upload_reel(self, video_path, caption):
        return self.client.clip_upload(video_path, caption=caption)