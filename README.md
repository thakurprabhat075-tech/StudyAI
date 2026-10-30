# StudyAI — beginner starter project

## 1. Requirements
- Windows 10/11
- Python installed
- Ollama installed and running
- Internet for initial model/package downloads

## 2. Setup in CMD
```bat
cd StudyAI
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
ollama pull llama3.2
```

## 3. Start the app
```bat
streamlit run app.py
```

Open the local URL Streamlit prints (usually http://localhost:8501).

## 4. Image questions
Image questions use the larger vision model. In a separate CMD, run:
```bat
ollama pull llama3.2-vision
```
This model is large and can require substantial RAM/VRAM. If the computer is low on memory, use text chat and notes first.

## 5. Voice
- Voice recording uses Streamlit's microphone input.
- Local transcription uses faster-whisper and may download a speech model on first use.
- Text-to-speech uses pyttsx3 and depends on Windows voices.
- If audio playback or a local audio dependency fails, the rest of the app should still work.

## 6. Data and limitations
- Profile, chats, notes and quiz scores are stored in `studyai.db` in this folder.
- This is a local learning prototype, not a multi-user production app. It does not have secure login/accounts.
- PDF extraction reads embedded text; scanned PDFs may need OCR.
- Quiz questions are AI-generated, so review answers before relying on them for exams.
