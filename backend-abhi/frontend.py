import streamlit as st
import requests
import os
import re

# API Endpoints
VIDEO_DOWNLOAD_URL = "http://127.0.0.1:5000/download_video"
AUDIO_DOWNLOAD_URL = "http://127.0.0.1:5000/download_audio"

def sanitize_filename(filename):
    """Remove invalid characters from filenames."""
    return re.sub(r'[<>:"/\\|?*]', '', filename)[:255]

st.title("Universal Media Downloader")

# Form for user input
with st.form("download_form"):
    # platform = st.selectbox("Platform", ["YouTube", "Twitter", "Instagram"])
    video_url = st.text_input("Enter Video URL:")
    quality = st.selectbox("Select Quality", ["best", "worst"])
    download_type = st.selectbox("Download Type", ["Video", "Audio"])
    # custom_filename = st.text_input("Optional: Enter Custom File Name (without extension)")
    submitted = st.form_submit_button("Download")

if submitted:
    if not video_url:
        st.error("Please provide a valid video URL.")
    else:
        # Decide API endpoint
        api_url = VIDEO_DOWNLOAD_URL if download_type == "Video" else AUDIO_DOWNLOAD_URL
        payload = {"url": video_url, "quality": quality}

        with st.spinner("Downloading..."):
            try:
                # Make API request
                response = requests.post(api_url, json=payload)
                if response.status_code == 200:
                    st.success("Download successful!")
                   
                else:
                    error_message = response.json().get("error", "Unknown error occurred.")
                    st.error(f"Error: {error_message}")
            except Exception as e:
                st.error(f"An error occurred: {e}")
