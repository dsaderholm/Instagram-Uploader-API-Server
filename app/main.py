from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import json
import sys
from instagram_client import InstagramClient
from audio_processor import AudioProcessor
import tempfile
import logging
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB limit

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_accounts():
    try:
        with open('/app/config/accounts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("accounts.json not found in /app/config/")
        raise
    except json.JSONDecodeError:
        logger.error("accounts.json is not valid JSON")
        raise

def cleanup_temp_files(files):
    """Safely cleanup temporary files"""
    for file_path in files:
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up {file_path}: {str(e)}")

def find_sound_file(sound_name):
    """Find a sound file regardless of case or spaces"""
    sounds_dir = '/app/sounds'
    try:
        # Strip any quotes from the sound name
        sound_name = sound_name.strip("'\"")
        logger.info(f"Looking for sound file with name: {sound_name}")
        
        # List all files in the sounds directory
        files = os.listdir(sounds_dir)
        logger.info(f"Available sound files: {files}")
        
        for filename in files:
            base_name = filename.lower().rsplit('.', 1)[0]
            logger.info(f"Comparing {base_name} with {sound_name.lower()}")
            if base_name == sound_name.lower():
                full_path = os.path.join(sounds_dir, filename)
                logger.info(f"Found matching sound file: {full_path}")
                return full_path
        logger.error(f"No matching sound file found for {sound_name}")
        return None
    except Exception as e:
        logger.error(f"Error searching for sound file: {str(e)}")
        return None

@app.route('/upload', methods=['POST'])
def upload_video():
    temp_files = []  # Keep track of temporary files to clean up

    try:
        # Validate request content type
        if not request.content_type or 'multipart/form-data' not in request.content_type:
            return jsonify({'error': 'Invalid content type. Must be multipart/form-data'}), 400

        # Check if video file is provided
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video = request.files['video']
        if not video or not video.filename:
            return jsonify({'error': 'No video file selected'}), 400
        
        if not allowed_file(video.filename):
            return jsonify({'error': f'Invalid file type. Allowed types are: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        # Get and validate parameters
        description = request.form.get('description', '')
        accountname = request.form.get('accountname')
        hashtags = request.form.get('hashtags', '').split(',') if request.form.get('hashtags') else []
        sound_name = request.form.get('sound_name')
        sound_aud_vol = request.form.get('sound_aud_vol', 'mix')

        if not accountname:
            return jsonify({'error': 'Account name is required'}), 400

        # Load account credentials
        try:
            accounts = load_accounts()
        except Exception as e:
            logger.error(f"Error loading accounts: {str(e)}")
            return jsonify({'error': 'Error loading account configuration'}), 500

        if accountname not in accounts:
            return jsonify({'error': 'Account not found'}), 404

        # Save video to a temporary file with a unique name
        temp_suffix = os.urandom(8).hex()
        temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{temp_suffix}.mp4')
        temp_files.append(temp_video.name)
        
        try:
            video.save(temp_video.name)
            logger.info(f"Video saved temporarily as {temp_video.name}")
        except Exception as e:
            logger.error(f"Error saving video file: {str(e)}")
            return jsonify({'error': 'Error saving video file'}), 500

        # Process audio if sound is specified
        final_video_path = temp_video.name
        if sound_name:
            sound_path = find_sound_file(sound_name)
            if not sound_path:
                logger.error(f"Sound file not found for name: {sound_name}")
                return jsonify({'error': f'Sound file not found: {sound_name}'}), 404
            
            try:
                processor = AudioProcessor()
                final_video_path = processor.mix_audio(
                    temp_video.name,
                    sound_path,
                    sound_aud_vol
                )
                temp_files.append(final_video_path)
                logger.info(f"Audio processing completed: {final_video_path}")
            except Exception as e:
                logger.error(f"Error processing audio: {str(e)}")
                return jsonify({'error': f'Error processing audio: {str(e)}'}), 500

        # Prepare caption with hashtags
        caption = description
        if hashtags and hashtags[0]:  # Only add hashtags if the list is not empty and first element is not empty
            # Remove any existing '#' from the hashtags before adding them
            cleaned_hashtags = [tag.strip().lstrip('#') for tag in hashtags if tag.strip()]
            caption += ' ' + ' '.join(f'#{tag}' for tag in cleaned_hashtags)

        # Upload to Instagram
        try:
            client = InstagramClient(
                accounts[accountname]['username'],
                accounts[accountname]['password']
            )
            
            media = client.upload_reel(final_video_path, caption)
            logger.info(f"Successfully uploaded video to Instagram. Media ID: {media.id}")
            
            return jsonify({
                'success': True,
                'message': 'Video uploaded successfully',
                'media_id': media.id
            })

        except Exception as e:
            logger.error(f"Error uploading to Instagram: {str(e)}")
            return jsonify({'error': f'Error uploading to Instagram: {str(e)}'}), 500

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Unexpected error in upload_video: {str(e)}\n{error_trace}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    
    finally:
        # Cleanup temporary files
        cleanup_temp_files(temp_files)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8048, debug=True)