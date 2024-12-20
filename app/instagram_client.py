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
        session_file = f'/app/config/sessions/{self.username}.json'
        
        if os.path.exists(session_file):
            try:
                self.client.load_settings(session_file)
                self.client.login(self.username, self.password, relogin=True)
                return
            except Exception:
                pass

        self.client.login(self.username, self.password)
        os.makedirs(os.path.dirname(session_file), exist_ok=True)
        self.client.dump_settings(session_file)

    def upload_reel(self, video_path, caption):
        return self.client.clip_upload(video_path, caption=caption)