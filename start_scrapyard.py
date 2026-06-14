import os
import sys
import subprocess
import uuid

# Auto-install minimal clean dependencies locally if missing
for pkg in ["fastapi", "uvicorn", "pydantic", "yt-dlp"]:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
import yt_dlp

app = FastAPI()

# Create target directories safely
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def cleanup_file(filepath: str):
    """Safely removes the file from disk after delivery is finished"""
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception:
            pass

@app.get("/")
def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.post("/api/analyze")
def check(req: dict):
    try:
        with yt_dlp.YoutubeDL({'extract_flat': True, 'quiet': True}) as ydl:
            info = ydl.extract_info(req["url"], download=False)
            return {"title": info.get("title", "Target Located")}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/download")
def get_media(url: str, mode: str, bg: BackgroundTasks):
    unique_id = str(uuid.uuid4())[:4]
    out = os.path.join(DOWNLOAD_DIR, f"{unique_id}_%(title)s.%(ext)s")
    opts = {'outtmpl': out, 'quiet': True, 'noplaylist': True}
    
    if mode == "original":
        opts['format'] = 'bestvideo+bestaudio/best'
    elif mode == "1080p":
        opts['format'] = 'bestvideo[height<=1080]+bestaudio/best'
    elif mode == "mp3": 
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file = ydl.prepare_filename(info)
            if mode == "mp3":
                file = os.path.splitext(file)[0] + ".mp3"
            
            # Pass the clean function to the background scheduler
            bg.add_task(cleanup_file, file)
            return FileResponse(file, media_type='application/octet-stream', filename=os.path.basename(file))
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
