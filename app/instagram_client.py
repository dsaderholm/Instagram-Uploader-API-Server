from instagrapi import Client
import os
import json
import stat

class InstagramClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.client = None
        self._login()

    def _login(self):
        self.client = Client()
        session_file = f'/app/config/sessions/{self.username}.json'
        session_dir = os.path.dirname(session_file)
        
        # Create directory with correct permissions if it doesn't exist
        if not os.path.exists(session_dir):
            os.makedirs(session_dir, mode=0o777, exist_ok=True)
            # Ensure the directory has the right permissions even if it already existed
            os.chmod(session_dir, 0o777)

        if os.path.exists(session_file):
            try:
                self.client.load_settings(session_file)
                self.client.login(self.username, self.password, relogin=True)
                return
            except Exception:
                pass

        self.client.login(self.username, self.password)
        
        # Write settings with correct permissions
        self.client.dump_settings(session_file)
        os.chmod(session_file, 0o666)  # Make file readable/writable by anyone

    def upload_reel(self, video_path, caption):
        return self.client.clip_upload(video_path, caption=caption)