from flask import Flask, request, jsonify, send_file, after_this_request
from src.insta_downloader import download_video_from_instagram, download_audio_from_instagram
from flask_cors import CORS
import os
import time
import threading
import atexit
import yt_dlp

app = Flask(__name__)
CORS(app)

# Keep track of files to clean up
cleanup_files = set()

def delayed_file_cleanup(filepath, delay=1):
    """Attempt to delete file with retry logic"""
    def cleanup():
        time.sleep(delay)  # Wait for file handles to be released
        retries = 3
        while retries > 0:
            try:
                if os.path.exists(filepath):
                    os.unlink(filepath)
                    print(f"Successfully cleaned up file: {filepath}")
                break
            except Exception as e:
                print(f"Cleanup attempt failed ({retries} retries left): {e}")
                retries -= 1
                time.sleep(1)
        if os.path.exists(filepath):
            cleanup_files.add(filepath)  # Add to cleanup set if failed

    thread = threading.Thread(target=cleanup)
    thread.daemon = True
    thread.start()

@atexit.register
def cleanup_remaining_files():
    """Clean up any remaining files when the application exits"""
    for filepath in cleanup_files:
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
                print(f"Cleaned up remaining file: {filepath}")
        except Exception as e:
            print(f"Failed to clean up file {filepath}: {e}")

@app.route('/')
def home():
    return 'Welcome to LinkLoader Downloader'

@app.route('/download_video_insta', methods=['POST'])
def download_video_insta():
    """API to download and return video data from Instagram reel."""
    data = request.get_json()
    url = data.get("url")
    video_file = None

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        video_file = download_video_from_instagram(url)

        if not os.path.exists(video_file):
            return jsonify({"error": "Video file not found"}), 500

        @after_this_request
        def cleanup(response):
            if video_file and os.path.exists(video_file):
                delayed_file_cleanup(video_file)
            return response

        return send_file(
            video_file,
            as_attachment=True,
            download_name=f"{url.split('/')[-2]}.mp4",
            mimetype="video/mp4"
        )

    except Exception as e:
        if video_file and os.path.exists(video_file):
            delayed_file_cleanup(video_file)
        return jsonify({"error": str(e)}), 500

@app.route('/download_audio_insta', methods=['POST'])
def download_audio_insta():
    """API to extract and return audio data from Instagram reel."""
    data = request.get_json()
    url = data.get("url")
    audio_file = None

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        audio_file = download_audio_from_instagram(url)

        if not os.path.exists(audio_file):
            return jsonify({"error": "Audio file not found"}), 500

        @after_this_request
        def cleanup(response):
            if audio_file and os.path.exists(audio_file):
                delayed_file_cleanup(audio_file)
            return response

        return send_file(
            audio_file,
            as_attachment=True,
            download_name=f"{url.split('/')[-2]}.mp3",
            mimetype="audio/mpeg"
        )

    except Exception as e:
        if audio_file and os.path.exists(audio_file):
            delayed_file_cleanup(audio_file)
        return jsonify({"error": str(e)}), 500

@app.route('/download_video', methods=['POST'])
def download_video():
    filename = None
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({"error": "URL is required"}), 400

        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'sanitize_filename': True,
            'cookies':'./cookies.txt',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            return jsonify({"error": "Video file not found"}), 500

        @after_this_request
        def cleanup(response):
            if filename and os.path.exists(filename):
                delayed_file_cleanup(filename)
            return response

        return send_file(
            filename,
            as_attachment=True,
            mimetype="video/mp4",
            download_name=f"{info['title']}.mp4"
        )

    except Exception as e:
        if filename and os.path.exists(filename):
            delayed_file_cleanup(filename)
        return jsonify({"error": str(e)}), 500

@app.route('/download_audio', methods=['POST'])
def download_audio():
    mp3_filename = None
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({"error": "URL is required"}), 400

        ydl_opts = {
            'format': 'bestaudio/best',
            'sanitize_filename': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            original_filename = ydl.prepare_filename(info)
            mp3_filename = original_filename.rsplit('.', 1)[0] + '.mp3'

        if not os.path.exists(mp3_filename):
            return jsonify({"error": "Audio file could not be created"}), 500

        @after_this_request
        def cleanup(response):
            if mp3_filename and os.path.exists(mp3_filename):
                delayed_file_cleanup(mp3_filename)
            return response

        return send_file(
            mp3_filename,
            as_attachment=True,
            mimetype="audio/mpeg",
            download_name=f"{info['title']}.mp3"
        )

    except Exception as e:
        if mp3_filename and os.path.exists(mp3_filename):
            delayed_file_cleanup(mp3_filename)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0')
