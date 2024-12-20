from instagrapi import Client
import json
import os

class InstagramClient:
    def __init__(self):
        self.accounts = self._load_accounts()
        self.clients = {}

    def _load_accounts(self):
        config_path = '/app/config/accounts.json'
        with open(config_path, 'r') as f:
            return json.load(f)

    def _get_client(self, accountname):
        if accountname not in self.clients:
            if accountname not in self.accounts:
                raise ValueError(f"Account {accountname} not configured")
            
            account = self.accounts[accountname]
            client = Client()
            session_file = f'/app/config/{accountname}_session.json'
            
            if os.path.exists(session_file):
                client.load_settings(session_file)
                client.login(account['username'], account['password'], relogin=True)
            else:
                client.login(account['username'], account['password'])
                client.dump_settings(session_file)
            
            self.clients[accountname] = client
        
        return self.clients[accountname]

    def upload_reel(self, accountname, video_path, caption):
        client = self._get_client(accountname)
        try:
            media = client.clip_upload(video_path, caption=caption)
            return {
                'success': True,
                'media_id': str(media.id),
                'caption': caption
            }
        except Exception as e:
            raise Exception(f"Failed to upload reel: {str(e)}")