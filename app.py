


import streamlit as st
import requests
import tempfile
import os
import re
from urllib.parse import urlparse
st.markdown("### Created by Nitin Khatri YT [@doitek](https://www.youtube.com/@doitek)")
def sanitize_filename(name):
    # Remove unsafe characters from filename
    return re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', name)

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except:
        return False

def download_file(url, temp_dir, progress_callback=None, stop_flag=None):
    # Sanitize filename from URL
    filename = url.split('/')[-1] or "downloaded_file"
    filename = sanitize_filename(filename)
    local_filename = os.path.join(temp_dir, filename)
    try:
        with requests.get(url, stream=True, timeout=15) as r:
            r.raise_for_status()
            total_length = r.headers.get('content-length')
            total_length = int(total_length) if total_length and total_length.isdigit() else 0
            downloaded = 0
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*32):
                    if stop_flag and stop_flag['stop']:
                        if os.path.exists(local_filename):
                            os.remove(local_filename)
                        return None  # Download stopped
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_length > 0:
                            progress_callback(downloaded / total_length)
        return local_filename, total_length
    except Exception as e:
        # Remove possibly partial file on error
        if os.path.exists(local_filename):
            os.remove(local_filename)
        return str(e), 0

# Initialize session state variables
if 'downloading' not in st.session_state:
    st.session_state.downloading = False
if 'stop' not in st.session_state:
    st.session_state.stop = False
if 'progress' not in st.session_state:
    st.session_state.progress = 0.0
if 'downloaded_file' not in st.session_state:
    st.session_state.downloaded_file = None
if 'file_size' not in st.session_state:
    st.session_state.file_size = 0
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'delete_file_flag' not in st.session_state:
    st.session_state.delete_file_flag = False

def log(message):
    st.session_state.logs.append(message)
    if len(st.session_state.logs) > 100:
        st.session_state.logs.pop(0)

st.title("Advanced File Downloader from URL")

url = st.text_input("Enter the direct file URL:")

col1, col2 = st.columns([1,1])
start_button = col1.button(
    "Start Download", 
    disabled=st.session_state.downloading or not url or not is_valid_url(url)
)
stop_button = col2.button("Stop Download", disabled=not st.session_state.downloading)

progress_bar = st.progress(0, text="Progress")
progress_text = st.empty()
status_text = st.empty()
path_text = st.empty()
size_text = st.empty()
error_text = st.empty()
log_container = st.expander("Logs", expanded=False)
log_area = log_container.empty()

# Update progress display
def progress_update(p):
    st.session_state.progress = p
    progress_bar.progress(p)
    percent = int(p * 100)
    progress_text.markdown(f"**Progress:** {percent}%")

if start_button:
    st.session_state.downloading = True
    st.session_state.stop = False
    st.session_state.progress = 0.0
    st.session_state.downloaded_file = None
    st.session_state.file_size = 0
    st.session_state.logs.clear()
    log("Download started.")
    status_text.text("Starting download...")

    temp_dir = tempfile.gettempdir()

    downloaded_file, total_length = download_file(
        url, 
        temp_dir=temp_dir, 
        progress_callback=progress_update,
        stop_flag=st.session_state
    )

    st.session_state.downloading = False

    if downloaded_file is None:
        log("Download stopped by user.")
        status_text.text("Download stopped.")
        progress_text.text("")
        path_text.text("")
        size_text.text("")
    elif isinstance(downloaded_file, str) and os.path.exists(downloaded_file):
        st.session_state.downloaded_file = downloaded_file
        st.session_state.file_size = total_length
        size_mb = total_length/(1024*1024)
        status_text.text("Download completed successfully!")
        path_text.text(f"File saved to temporary location:\n`{downloaded_file}`")
        size_text.text(f"File Size: {size_mb:.2f} MB")
        log(f"File downloaded: {downloaded_file} ({size_mb:.2f} MB)")
    else:
        error_msg = downloaded_file
        status_text.text("")
        progress_text.text("")
        size_text.text("")
        path_text.text("")
        error_text.error(f"Download error: {error_msg}")
        log(f"Error: {error_msg}")

if stop_button and st.session_state.downloading:
    st.session_state.stop = True
    log("Stop requested by user.")

if st.session_state.downloaded_file and not st.session_state.downloading:
    with open(st.session_state.downloaded_file, "rb") as file:
        if st.download_button(
            label=f"Download {os.path.basename(st.session_state.downloaded_file)}",
            data=file,
            file_name=os.path.basename(st.session_state.downloaded_file),
            mime="application/octet-stream"
        ):
            # Mark file for deletion after this interaction
            st.session_state.delete_file_flag = True

# Delete file only on the next rerun to avoid "file-in-use" errors on Windows
if st.session_state.delete_file_flag:
    try:
        os.remove(st.session_state.downloaded_file)
        path_text.text("Temporary file deleted after download.")
        st.session_state.downloaded_file = None
        progress_bar.progress(0)
        progress_text.text("")
        status_text.text("")
        size_text.text("")
        st.session_state.delete_file_flag = False
        log("Temporary file deleted after download.")
    except Exception as e:
        error_text.error(f"Failed to delete temporary file: {e}")
        log(f"Error deleting temp file: {e}")

# Display logs with limit and scroll
log_area.text('\n'.join(st.session_state.logs[-100:]))

if not url:
    st.warning("Please enter a valid URL to enable download.")
elif not is_valid_url(url):
    st.error("Invalid URL format. Please enter a valid HTTP or HTTPS URL.")
