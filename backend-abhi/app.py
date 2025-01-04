import os
from flask import Flask, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 *1024
# Route to download video
@app.route('/download_video', methods=['POST'])
@app.route('/download_video', methods=['POST'])
def download_video():
    try:
        data = request.json
        url = data.get('url')
        quality = data.get('quality', 'best')  # Default to best quality

        if not url:
            return jsonify({"error": "URL is required"}), 400

        # Update to download max quality video and audio together
        ydl_opts = {
            'format': 'best',  # Best video and best audio
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'sanitize_filename': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return send_file(filename, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to download audio
@app.route('/download_audio', methods=['POST'])
def download_audio():
    try:
        data = request.json
        url = data.get('url')

        if not url:
            return jsonify({"error": "URL is required"}), 400

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return send_file(filename, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    app.run(debug=True)
