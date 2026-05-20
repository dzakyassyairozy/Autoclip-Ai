# ✂️ Auto Clip Viral AI

Aplikasi berbasis web untuk memotong video YouTube atau file lokal secara otomatis menggunakan AI (Gemini + Whisper) untuk kebutuhan konten TikTok/Shorts.

## 🛠️ Fitur Utama
- **Auto Transcript:** Mengambil subtitle otomatis dari YouTube atau via file lokal dengan OpenAI Whisper.
- **AI Viral Hook Finder:** Menggunakan Google Gemini 2.5 Flash untuk menemukan detik paling potensial untuk viral.
- **Auto Video Cutter:** Pemotongan otomatis menggunakan library FFmpeg tanpa merusak kualitas video asal.

## 🚀 Cara Install & Jalankan
1. Clone repository ini.
2. Install library: `pip install -r requirements.txt`
3. Jalankan server: `uvicorn main:app --reload`
