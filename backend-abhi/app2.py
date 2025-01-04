import os
from flask import Flask, request, jsonify, send_file, after_this_request
import yt_dlp
from flask_cors import CORS
import threading
import time
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

# Route to download video
@app.route('/download_video', methods=['POST'])
def download_video():
    """API to download and return video data"""
    data = request.get_json()
    url = data.get("url")
    quality = data.get("quality", "best")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        # Use yt-dlp to download the video with the requested quality
        ydl_opts = {
            'format': quality,
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'noplaylist': True,
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Serve the file directly to the browser for download
        response = send_file(
            filename,
            as_attachment=True,
            download_name=f"{info['title']}.mp4",  # Name of the video file
            mimetype="video/mp4"
        )

        @response.call_on_close
        def cleanup_after_send():
            if os.path.exists(filename):
                delayed_file_cleanup(filename)

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to download audio
@app.route('/download_audio', methods=['POST'])
def download_audio():
    """API to extract and return audio data"""
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Serve the audio file directly to the browser for download
        response = send_file(
            filename,
            as_attachment=True,
            download_name=f"{info['title']}.mp3",  # Name of the audio file
            mimetype="audio/mpeg"
        )

        @response.call_on_close
        def cleanup_after_send():
            if os.path.exists(filename):
                delayed_file_cleanup(filename)

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
