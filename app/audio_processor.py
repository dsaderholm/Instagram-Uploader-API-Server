import subprocess
import os

class AudioProcessor:
    def mix_audio(self, video_path, sound_path, mix_type='mix'):
        output_path = f"{os.path.splitext(video_path)[0]}_with_sound.mp4"
        
        # Set volume levels based on mix type
        if mix_type == 'background':
            orig_vol = 1.0
            sound_vol = 0.3
        elif mix_type == 'main':
            orig_vol = 0.3
            sound_vol = 1.0
        else:  # mix
            orig_vol = 0.5
            sound_vol = 0.5

        # FFmpeg command to mix audio
        cmd = [
            'ffmpeg', '-i', video_path,
            '-i', sound_path,
            '-filter_complex',
            f'[0:a]volume={orig_vol}[a1];[1:a]volume={sound_vol}[a2];[a1][a2]amix=inputs=2:duration=first[aout]',
            '-map', '0:v', '-map', '[aout]',
            '-c:v', 'copy',
            '-shortest',
            output_path
        ]

        subprocess.run(cmd, check=True)
        return output_path