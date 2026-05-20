import os
import json
import subprocess
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from google import genai
from youtube_transcript_api import YouTubeTranscriptApi

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Membuat folder temp otomatis untuk menampung video di server
os.makedirs("temp", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Menampilkan halaman utama website saat pertama kali dibuka
    return templates.TemplateResponse("index.html", {"request": request, "result": None})

@app.post("/process", response_class=HTMLResponse)
async def process_video(
    request: Request, 
    api_key: str = Form(...), 
    url_youtube: str = Form(None), 
    uploaded_file: UploadFile = File(None)
):
    transcript_text_with_time = ""
    video_source = ""
    
    # 1. PROSES AMBIL SUBTITLE / TRANSKRIP
    # Jika user memasukkan link YouTube
    if url_youtube and ("youtu.be/" in url_youtube or "v=" in url_youtube):
        try:
            if "youtu.be/" in url_youtube:
                video_id = url_youtube.split("youtu.be/")[1].split("?")[0]
            else:
                video_id = url_youtube.split("v=")[1].split("&")[0]
                
            srv_transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['id', 'en'])
            for seg in srv_transcript:
                start = seg['start']
                end = start + seg['duration']
                transcript_text_with_time += f"[{start:.2f} - {end:.2f}] {seg['text']}\n"
            video_source = "youtube"
        except Exception:
            pass

    # Jika jalur YouTube gagal atau user memilih upload file video dari HP
    if not transcript_text_with_time and uploaded_file and uploaded_file.filename:
        file_path = f"temp/{uploaded_file.filename}"
        with open(file_path, "wb") as f:
            f.write(await uploaded_file.read())
            
        # Whisper AI memproses audio dari file lokal
        import whisper
        model_whisper = whisper.load_model("tiny")
        result = model_whisper.transcribe(file_path)
        for seg in result["segments"]:
            transcript_text_with_time += f"[{seg['start']:.2f} - {seg['end']:.2f}] {seg['text']}\n"
        
        os.rename(file_path, "temp/video_asli.mp4")
        video_source = "upload"

    # Jika kedua jalur gagal mendapatkan teks
    if not transcript_text_with_time:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Gagal mengambil transkrip/subtitle video. Pastikan video punya subtitle atau file video valid."})

    # 2. ANALISIS MOMEN VIRAL PAKAI GEMINI AI
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        Analisis teks durasi ini, cari 1 bagian paling viral (durasi ideal 15-40 detik). 
        Wajib memberikan respon akhir dalam format JSON murni seperti ini:
        {{
          "kalimat_viral": "isi kalimatnya di sini",
          "detik_mulai": 12.5,
          "detik_selesai": 35.2
        }}
        
        Berikut datanya:
        {transcript_text_with_time}
        """
        
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        ai_decision = json.loads(raw_text)
        
        start_time = ai_decision['detik_mulai']
        duration = ai_decision['detik_selesai'] - start_time
        output_filename = "temp/klip_viral_publik.mp4"
        
        # 3. PEMOTONGAN OTOMATIS PAKAI FFMPEG
        if video_source == "youtube":
            # Ambil link streaming langsung dari YouTube via yt-dlp
            get_url_cmd = f'yt-dlp -g -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best" {url_youtube}'
            stream_urls = subprocess.check_output(get_url_cmd, shell=True).decode('utf-8').strip().split('\n')
            cmd = f'ffmpeg -y -ss {start_time} -i "{stream_urls[0]}" -ss {start_time} -i "{stream_urls[1]}" -t {duration
      
