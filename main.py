from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
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

# Universal configuration to bypass security challenges
BASE_YTDL_OPTS = {
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    # Forces a generic browser identity so platforms don't instantly flag the script
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Sec-Fetch-Mode': 'navigate',
    }
}

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/analyze")
def analyze_link(request: LinkRequest):
    opts = dict(BASE_YTDL_OPTS)
    opts['extract_flat'] = True  # Fast scan without downloading chunks
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            if not info:
                raise Exception("Empty metadata package returned.")
            return {
                "title": info.get("title", "Target Video Target Located"),
                "source": info.get("extractor_key", "Web Stream")
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/download")
def download_media(url: str, mode: str, background_tasks: BackgroundTasks):
    unique_id = str(uuid.uuid4())[:6]
    out_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}_%(title)s.%(ext)s")
    
    ydl_opts = dict(BASE_YTDL_OPTS)
    ydl_opts['outtmpl'] = out_template

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
            
            if mode == "mp3":
                filename = os.path.splitext(filename)[0] + ".mp3"
                
        if os.path.exists(filename):
            background_tasks.add_task(remove_temp_file, filename)
            return FileResponse(path=filename, media_type='application/octet-stream', filename=os.path.basename(filename))
        else:
            raise HTTPException(status_code=500, detail="File compilation error.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
