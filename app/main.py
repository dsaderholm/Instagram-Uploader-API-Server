from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import json
from instagram_client import InstagramClient
from audio_processor import AudioProcessor
import tempfile

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_accounts():
    with open('/app/config/accounts.json', 'r') as f:
        return json.load(f)

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    video = request.files['video']
    if not video or not allowed_file(video.filename):
        return jsonify({'error': 'Invalid video file'}), 400

    # Get parameters
    description = request.form.get('description', '')
    accountname = request.form.get('accountname')
    hashtags = request.form.get('hashtags', '').split(',')
    sound_name = request.form.get('sound_name')
    sound_aud_vol = request.form.get('sound_aud_vol', 'mix')

    if not accountname:
        return jsonify({'error': 'Account name is required'}), 400

    # Load account credentials
    accounts = load_accounts()
    if accountname not in accounts:
        return jsonify({'error': 'Account not found'}), 404

    # Save video temporarily
    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    video.save(temp_video.name)

    try:
        # Process audio if sound is specified
        final_video_path = temp_video.name
        if sound_name:
            processor = AudioProcessor()
            sound_path = f'/app/sounds/{sound_name}.mp3'
            if not os.path.exists(sound_path):
                return jsonify({'error': 'Sound file not found'}), 404
            
            final_video_path = processor.mix_audio(
                temp_video.name,
                sound_path,
                sound_aud_vol
            )

        # Prepare caption with hashtags
        caption = description
        if hashtags:
            caption += ' ' + ' '.join(hashtags)

        # Upload to Instagram
        client = InstagramClient(
            accounts[accountname]['username'],
            accounts[accountname]['password']
        )
        
        media = client.upload_reel(final_video_path, caption)
        
        return jsonify({
            'success': True,
            'message': 'Video uploaded successfully',
            'media_id': media.id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Cleanup temporary files
        os.unlink(temp_video.name)
        if final_video_path != temp_video.name:
            os.unlink(final_video_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8048)