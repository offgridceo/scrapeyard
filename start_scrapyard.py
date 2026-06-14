import os, sys, subprocess

# Force download the two basic required packages if missing
for pkg in ["fastapi", "uvicorn", "yt-dlp"]:
    try: __import__(pkg)
    except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
import yt_dlp, uuid

app = FastAPI()
os.makedirs("downloads", exist_ok=True)

@app.get("/")
def home():
    with open("index.html", "r", encoding="utf-8") as f: 
        return HTMLResponse(f.read())

@app.get("/api/download")
def get_media(url: str, bg: BackgroundTasks):
    # Forces standard 1080p height ceiling, falling back to lower if 1080p isn't available
    out = os.path.join("downloads", f"{str(uuid.uuid4())[:4]}_video.mp4")
    opts = {
        'outtmpl': out, 
        'quiet': True, 
        'noplaylist': True,
        'format': 'bestvideo[height<=1080]+bestaudio/best',
        'merge_output_format': 'mp4'
    }
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file = ydl.prepare_filename(info)
        
        # This auto-deletes the heavy video file from your drive after your browser finishes grabbing it
        bg.add_task(lambda f: os.path.exists(f) and os.remove(f), file)
        return FileResponse(file, media_type='application/octet-stream', filename="scrapyard_video.mp4")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
