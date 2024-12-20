from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from .instagram_client import InstagramClient
from .audio_processor import AudioProcessor
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = '/app/uploads'
app.config['SOUNDS_FOLDER'] = '/app/sounds'

ALLOWED_EXTENSIONS = {'mp4', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_video():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video = request.files['video']
        if not allowed_file(video.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        accountname = request.form.get('accountname')
        if not accountname:
            return jsonify({'error': 'Account name is required'}), 400

        description = request.form.get('description', '')
        hashtags = request.form.get('hashtags', '').split(',')
        sound_name = request.form.get('sound_name')
        sound_aud_vol = request.form.get('sound_aud_vol', 'mix')

        # Save uploaded video
        video_filename = secure_filename(video.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        video.save(video_path)

        # Process audio if sound requested
        final_video_path = video_path
        if sound_name:
            sound_path = os.path.join(app.config['SOUNDS_FOLDER'], f"{sound_name}.mp3")
            if os.path.exists(sound_path):
                processor = AudioProcessor()
                final_video_path = processor.mix_audio(
                    video_path, 
                    sound_path,
                    sound_aud_vol
                )
            else:
                return jsonify({'error': f'Sound {sound_name} not found'}), 404

        # Prepare caption with hashtags
        caption = description
        if hashtags:
            caption += ' ' + ' '.join(f"#{tag.strip('#')}" for tag in hashtags if tag)

        # Upload to Instagram
        client = InstagramClient()
        result = client.upload_reel(accountname, final_video_path, caption)

        # Cleanup
        os.remove(video_path)
        if final_video_path != video_path:
            os.remove(final_video_path)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8048)