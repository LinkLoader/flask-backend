import instaloader
from moviepy.video.io.VideoFileClip import VideoFileClip
import tempfile
import os
import requests

# Initialize Instaloader
loader = instaloader.Instaloader(
    download_pictures=False,
    download_comments=False,
    download_geotags=False,
    save_metadata=False,
    download_video_thumbnails=False,
)

def extract_shortcode(url):
    """Extract shortcode from Instagram URL."""
    try:
        return url.split("/")[-2]
    except IndexError:
        return None

def download_video_from_instagram(url):
    """Download video from Instagram URL and return the file path."""
    shortcode = extract_shortcode(url)
    if not shortcode:
        raise ValueError("Invalid URL format")

    temp_video = None
    try:
        # Get Post object
        post = instaloader.Post.from_shortcode(loader.context, shortcode)

        # Get video URL directly
        if not post.is_video:
            raise ValueError("This post does not contain a video")

        video_url = post.video_url
        # print(f"Video URL: {video_url}")

        # Create temporary file
        temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)

        # Download video directly
        # print(f"Downloading to: {temp_video.name}")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()

        # Write content to file
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_video.write(chunk)

        # Close the file
        temp_video.close()

        # Verify file exists and has content
        if not os.path.exists(temp_video.name):
            raise ValueError("Failed to save video file")

        file_size = os.path.getsize(temp_video.name)
        # print(f"Downloaded file size: {file_size} bytes")

        if file_size == 0:
            raise ValueError("Downloaded video file is empty")

        return temp_video.name

    except Exception as e:
        # print(f"Error during download: {str(e)}")
        if temp_video and hasattr(temp_video, 'name') and os.path.exists(temp_video.name):
            try:
                os.unlink(temp_video.name)
            except Exception as del_e:
                print(f"Error deleting temp file: {del_e}")
        raise

def download_audio_from_instagram(url):
    """Extract and return audio from Instagram reel."""
    video_file = download_video_from_instagram(url)
    temp_audio = None

    try:
        # Create temporary file for audio
        temp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_audio.close()

        # Extract audio from video
        clip = VideoFileClip(video_file)
        clip.audio.write_audiofile(temp_audio.name)
        clip.close()

        # Clean up the video file
        try:
            os.unlink(video_file)
        except Exception as e:
            print(f"Error deleting video file: {e}")

        return temp_audio.name

    except Exception as e:
        if temp_audio and os.path.exists(temp_audio.name):
            try:
                os.unlink(temp_audio.name)
            except Exception as del_e:
                print(f"Error deleting temp audio file: {del_e}")
        raise e
