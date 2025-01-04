from flask import Flask, request, jsonify, send_file, after_this_request
from src.insta_downloader import download_video_from_instagram, download_audio_from_instagram
from flask_cors import CORS
import os
import time
import threading
import atexit

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
        except Exception as e:
            print(f"Failed to clean up file {filepath}: {e}")

@app.route('/')
def home():
    return 'Welcome to Instagram Downloader'

@app.route('/download_video', methods=['POST'])
def download_video():
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

        response = send_file(
            video_file,
            as_attachment=True,
            download_name=f"{url.split('/')[-2]}.mp4",
            mimetype="video/mp4"
        )

        @response.call_on_close
        def cleanup_after_send():
            if video_file:
                delayed_file_cleanup(video_file)

        return response

    except Exception as e:
        if video_file and os.path.exists(video_file):
            delayed_file_cleanup(video_file)
        return jsonify({"error": str(e)}), 500

@app.route('/download_audio', methods=['POST'])
def download_audio():
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

        response = send_file(
            audio_file,
            as_attachment=True,
            download_name=f"{url.split('/')[-2]}.mp3",
            mimetype="audio/mpeg"
        )

        @response.call_on_close
        def cleanup_after_send():
            if audio_file:
                delayed_file_cleanup(audio_file)

        return response

    except Exception as e:
        if audio_file and os.path.exists(audio_file):
            delayed_file_cleanup(audio_file)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
