from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class LinkRequest(BaseModel):
    url: str

def remove_temp_file(filepath: str):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/analyze")
def analyze_link(request: LinkRequest):
    try:
        with yt_dlp.YoutubeDL({'noplaylist': True, 'extract_flat': True}) as ydl:
            info = ydl.extract_info(request.url, download=False)
            return {
                "title": info.get("title", "Target Video Data Fetched"),
                "source": info.get("extractor_key", "Web Stream")
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/download")
def download_media(url: str, mode: str, background_tasks: BackgroundTasks):
    unique_id = str(uuid.uuid4())[:6]
    out_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}_%(title)s.%(ext)s")
    
    ydl_opts = {
        'outtmpl': out_template,
        'noplaylist': True,
        'quiet': True,
    }

    if mode == "original":
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    elif mode == "1080p":
        ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best'
    elif mode == "mp3":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Resolve extension mismatch if post-processor ran
            if mode == "mp3":
                filename = os.path.splitext(filename)[0] + ".mp3"
                
        if os.path.exists(filename):
            background_tasks.add_task(remove_temp_file, filename)
            return FileResponse(path=filename, media_type='application/octet-stream', filename=os.path.basename(filename))
        else:
            raise HTTPException(status_code=500, detail="File encoding error.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
