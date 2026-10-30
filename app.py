import io
import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st
from openai import OpenAI
from PIL import Image

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "studyai.db"
TEXT_MODEL = "llama3.2"
VISION_MODEL = "llama3.2-vision"
# -------------------- LM STUDIO --------------------
client = OpenAI(
    base_url="http://localhost:1234/v1",
    api_key="lm-studio"
)

st.set_page_config(page_title="StudyAI", page_icon="🎓", layout="wide")

# -------------------- DATABASE --------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT DEFAULT 'Student',
                class_name TEXT DEFAULT '',
                goal TEXT DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                kind TEXT NOT NULL,
                subject TEXT,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL
            )
        """)
        conn.execute("INSERT OR IGNORE INTO profile (id, name) VALUES (1, 'Student')")

def get_profile():
    with get_conn() as conn:
        return dict(conn.execute("SELECT * FROM profile WHERE id=1").fetchone())

def save_profile(name, class_name, goal):
    with get_conn() as conn:
        conn.execute(
            "UPDATE profile SET name=?, class_name=?, goal=? WHERE id=1",
            (name.strip() or "Student", class_name.strip(), goal.strip())
        )

def save_history(kind, subject, prompt, response):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO history (created_at, kind, subject, prompt, response) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), kind, subject, prompt, response)
        )

def ask_ai(prompt, model=None, image_bytes=None, system=None):
    import os
    import io
    from dotenv import load_dotenv
    from google import genai
    from PIL import Image

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "Error: GEMINI_API_KEY .env file mein nahi mili."

    try:
        client = genai.Client(api_key=api_key)

        full_prompt = (
            (system or "You are StudyAI, a helpful college tutor. "
             "Answer clearly in simple English with correct examples.")
            + "\n\nStudent question: "
            + str(prompt)
        )

        contents = [full_prompt]

        if image_bytes:
            image = Image.open(io.BytesIO(image_bytes))
            contents.append(image)

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=contents
        )

        return response.text or "Gemini returned an empty answer."

    except Exception as e:
        return f"Gemini API error: {e}"


def check_ollama():
    import os
    from dotenv import load_dotenv

    load_dotenv()
    if os.getenv("GEMINI_API_KEY"):
        return True, ""
    return False, "GEMINI_API_KEY .env file mein nahi mili."


init_db()
profile = get_profile()

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.title("🎓 StudyAI")
    st.caption("Your personal local AI tutor")
    page = st.radio(
        "Navigation",
        ["Dashboard", "AI Chat", "Create Notes", "Quiz Generator", "History", "My Profile"],
        label_visibility="visible"
    )
    st.divider()
    st.caption("Local AI • No API key")
    st.caption(f"Student: {profile['name']}")

SUBJECTS = [
    "General", "Mathematics", "Physics", "Chemistry", "Computer Science",
    "English", "Biology", "Digital Electronics", "Data Structures", "OOPs"
]
DIFFICULTIES = ["Easy", "Medium", "Hard"]
QUESTION_TYPES = ["Explain a concept", "MCQ", "Short answer", "Long answer", "Step-by-step solution"]
LANGUAGES = ["Simple English", "Hindi", "Hinglish"]

def subject_settings(prefix):
    c1, c2, c3 = st.columns(3)
    subject = c1.selectbox("Subject", SUBJECTS, key=f"{prefix}_subject")
    difficulty = c2.selectbox("Difficulty", DIFFICULTIES, key=f"{prefix}_difficulty")
    language = c3.selectbox("Answer language", LANGUAGES, key=f"{prefix}_language")
    return subject, difficulty, language

def model_status():
    ok, err = check_ollama()
    if ok:
        st.success("Ollama is reachable.")
    else:
        st.error("Ollama se connection nahi ho raha. Check karo ki Ollama install aur running hai.")
        st.code("ollama list")
        st.caption(err)

# -------------------- DASHBOARD --------------------
if page == "Dashboard":
    st.title(f"Welcome, {profile['name']} 👋")
    st.write("Learn topics, ask questions, create notes and practise with quizzes.")
    ok, err = check_ollama()
    if ok:
        st.success("Local AI connection: Ready")
    else:
        st.warning("Local AI connection not detected. Start Ollama and run `ollama pull llama3.2`.")
    with get_conn() as conn:
        total_chats = conn.execute("SELECT COUNT(*) FROM history WHERE kind='chat'").fetchone()[0]
        total_notes = conn.execute("SELECT COUNT(*) FROM history WHERE kind='notes'").fetchone()[0]
        quiz_count = conn.execute("SELECT COUNT(*) FROM quiz_results").fetchone()[0]
        result = conn.execute("SELECT COALESCE(SUM(score),0), COALESCE(SUM(total),0) FROM quiz_results").fetchone()
        score_sum, total_sum = result[0], result[1]
        recent = conn.execute("SELECT created_at, kind, subject, prompt FROM history ORDER BY id DESC LIMIT 5").fetchall()
    accuracy = round(score_sum * 100 / total_sum) if total_sum else 0
    a, b, c, d = st.columns(4)
    a.metric("Chat questions", total_chats)
    b.metric("Notes created", total_notes)
    c.metric("Quizzes taken", quiz_count)
    d.metric("Quiz accuracy", f"{accuracy}%")
    st.subheader("Recent activity")
    if recent:
        for row in recent:
            st.write(f"**{row['created_at']} · {row['kind'].title()} · {row['subject']}**")
            st.caption(row["prompt"][:160])
    else:
        st.info("Abhi activity nahi hai. AI Chat ya Create Notes se shuru karo.")
    st.subheader("Quick tips")
    st.markdown("- Chat mein topic ko apne words mein explain karne ko kaho.\n- Quiz ke baad explanations padho.\n- Profile mein apna learning goal set karo.")

# -------------------- AI CHAT --------------------
elif page == "AI Chat":
    st.title("💬 AI Study Chat")
    st.write("Text question poochho, image upload karo, ya voice recording do.")
    subject, difficulty, language = subject_settings("chat")
    qtype = st.selectbox("Question type", QUESTION_TYPES, key="chat_qtype")
    uploaded_image = st.file_uploader("Optional: question ki image upload karo", type=["png", "jpg", "jpeg"], key="chat_image")
    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded question image", width=300)

    with st.expander("🎙️ Voice input (optional)"):
        audio_value = st.audio_input("Record your question")
        if audio_value:
            st.audio(audio_value)
            if st.button("Transcribe voice locally"):
                try:
                    from faster_whisper import WhisperModel
                    with st.spinner("Local speech model load ho raha hai..."):
                        whisper = WhisperModel("base", device="cpu", compute_type="int8")
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                            tmp.write(audio_value.getvalue())
                            audio_path = tmp.name
                        segments, info = whisper.transcribe(audio_path)
                        transcript = " ".join(seg.text.strip() for seg in segments).strip()

                    st.session_state["voice_transcript"] = transcript
                    st.session_state["chat_question"] = transcript
                    st.success("Transcription ready. Neeche text box mein check/edit kar sakte ho.")
                except Exception as e:
                    st.error(f"Voice transcription error: {e}")
                    st.info("Check karo `pip install faster-whisper` complete hua ho. Pehli baar model download bhi ho sakta hai.")

    if "chat_question" not in st.session_state:
        st.session_state["chat_question"] = ""

    if "voice_transcript" not in st.session_state:
        st.session_state["voice_transcript"] = ""

    default_question = st.session_state.get("voice_transcript", "")

    question = st.text_area(
        "Your question",
        value=default_question,
        placeholder="Example: Explain binary search with an example.",
        height=110,
        key="chat_question"
    )

    if st.button("Ask StudyAI", type="primary"):
        if not question.strip() and not uploaded_image:
            st.warning("Question likho ya image upload karo.")
        else:
            prompt = (
                f"You are a friendly study tutor. Subject: {subject}. Difficulty: {difficulty}. "
                f"Question type: {qtype}. Answer in {language}. Explain accurately and clearly, "
                "using steps and examples when helpful. If the image contains a question, read it carefully. "
                "If any text is unreadable, say so instead of guessing.\n\n"
                f"Student question: {question.strip() or 'Please read and solve the uploaded image.'}"
            )
            image_bytes = uploaded_image.getvalue() if uploaded_image else None
            model = VISION_MODEL if image_bytes else TEXT_MODEL
            try:
                with st.spinner("StudyAI is thinking..."):
                    answer = ask_ai(prompt, model=model, image_bytes=image_bytes)
                st.session_state["last_answer"] = answer
                save_history("chat", subject, question.strip() or "[Image question]", answer)
            except Exception as e:
                st.error(f"AI error: {e}")
                if image_bytes:
                    st.info("Image questions ke liye `ollama pull llama3.2-vision` chalao. Vision model ko kaafi disk/RAM resources chahiye.")
                else:
                    st.info("CMD mein `ollama list` aur `ollama run llama3.2` se check karo ki model available hai.")

    if st.session_state.get("last_answer"):
        st.markdown("### Latest Answer")
        st.markdown(st.session_state["last_answer"])
        if st.button("🔊 Read latest answer aloud"):
            try:
                import pyttsx3
                engine = pyttsx3.init()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    audio_path = tmp.name
                engine.save_to_file(st.session_state["last_answer"], audio_path)
                engine.runAndWait()
                st.audio(Path(audio_path).read_bytes(), format="audio/wav")
            except Exception as e:
                st.error(f"Text-to-speech error: {e}")

# -------------------- NOTES --------------------
elif page == "Create Notes":
    st.title("📝 AI Notes Creator")
    st.write("Topic ya PDF se revision notes banao.")
    subject, difficulty, language = subject_settings("notes")
    topic = st.text_input("Topic", placeholder="Example: B-tree in data structures")
    pdf = st.file_uploader("Optional: PDF upload karo", type=["pdf"], key="notes_pdf")
    if st.button("Generate notes", type="primary"):
        if not topic.strip() and not pdf:
            st.warning("Topic likho ya PDF upload karo.")
        else:
            source_text = ""
            if pdf:
                try:
                    import fitz
                    doc = fitz.open(stream=pdf.getvalue(), filetype="pdf")
                    source_text = "\n".join(page.get_text() for page in doc)
                    source_text = source_text[:18000]
                    if not source_text.strip():
                        st.warning("PDF se readable text nahi mila. Scanned PDF ke liye OCR ki zaroorat ho sakti hai.")
                except Exception as e:
                    st.error(f"PDF read error: {e}")
            prompt = (
                f"Create clear study notes for subject {subject}, topic {topic or 'uploaded PDF content'}. "
                f"Use {language}. Difficulty/audience: {difficulty}. Include definition, key points, "
                "examples, important terms and a short summary. Do not invent facts outside the source when source text is provided.\n\n"
                f"PDF source text:\n{source_text if source_text else '(No PDF text provided; use the topic.)'}"
            )
            try:
                with st.spinner("Notes ban rahe hain..."):
                    notes = ask_ai(prompt)
                st.markdown(notes)
                save_history("notes", subject, topic or pdf.name, notes)
                st.download_button("Download notes as TXT", data=notes, file_name="study_notes.txt", mime="text/plain")
            except Exception as e:
                st.error(f"AI error: {e}")

# -------------------- QUIZ --------------------
elif page == "Quiz Generator":
    st.title("🧠 Quiz Generator")
    subject, difficulty, language = subject_settings("quiz")
    topic = st.text_input("Quiz topic", placeholder="Example: Python variables")
    number = st.slider("Number of questions", min_value=3, max_value=10, value=5)
    if st.button("Create quiz", type="primary"):
        if not topic.strip():
            st.warning("Quiz topic likho.")
        else:
            prompt = (
                f"Create exactly {number} multiple-choice questions about {topic} in {subject}. "
                f"Difficulty: {difficulty}. Language: {language}. Return ONLY valid JSON array, no markdown. "
                'Each object must have keys: "question", "options" (array of exactly 4 strings), '
                '"answer" (one option copied exactly from options), and "explanation" (string).'
            )
            try:
                with st.spinner("Quiz ban raha hai..."):
                    raw = ask_ai(prompt)
                cleaned = raw.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                questions = json.loads(cleaned)
                if not isinstance(questions, list) or not questions:
                    raise ValueError("Model ne expected quiz list return nahi ki.")
                st.session_state["quiz_questions"] = questions
                st.session_state["quiz_topic"] = topic
                
                st.session_state["quiz_submitted"] = False
            except Exception as e:
                st.error(f"Quiz create/parse error: {e}")
                st.info("Dobara try karo ya questions ki sankhya kam karo.")
    questions = st.session_state.get("quiz_questions", [])
    if questions:
        st.subheader(f"Quiz: {st.session_state.get('quiz_topic', '')}")
        with st.form("quiz_form"):
            answers = []
            for i, item in enumerate(questions):
                st.markdown(f"**Q{i+1}. {item.get('question', 'Question missing')}**")
                options = item.get("options", [])
                if not options:
                    options = ["Option A", "Option B", "Option C", "Option D"]
                answers.append(st.radio("Choose an answer", options, key=f"quiz_answer_{i}", index=None))
            submitted = st.form_submit_button("Submit quiz")
        if submitted:
            score = 0
            for i, item in enumerate(questions):
                if answers[i] == item.get("answer"):
                    score += 1
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO quiz_results (created_at, subject, topic, score, total) VALUES (?, ?, ?, ?, ?)",
                    (datetime.now().strftime("%Y-%m-%d %H:%M"), st.session_state.get("quiz_subject", subject),
                     st.session_state.get("quiz_topic", topic), score, len(questions))
                )
            st.session_state["quiz_submitted"] = True
            st.session_state["quiz_score"] = score
            st.rerun()
        if st.session_state.get("quiz_submitted"):
            score = st.session_state.get("quiz_score", 0)
            st.success(f"Score: {score}/{len(questions)} ({round(score*100/len(questions))}%)")
            for i, item in enumerate(questions):
                st.markdown(f"**Q{i+1}. {item.get('question', '')}**")
                st.write(f"Correct answer: {item.get('answer', 'Not provided')}")
                st.caption(item.get("explanation", ""))

# -------------------- HISTORY --------------------
elif page == "History":
    st.title("🕘 History")
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM history ORDER BY id DESC LIMIT 200").fetchall()
        quizzes = conn.execute("SELECT * FROM quiz_results ORDER BY id DESC LIMIT 100").fetchall()
    st.subheader("Chats and notes")
    if not rows:
        st.info("Abhi history empty hai.")
    for row in rows:
        with st.expander(f"{row['created_at']} · {row['kind'].title()} · {row['subject']} · {row['prompt'][:60]}"):
            st.markdown("**Question / Topic**")
            st.write(row["prompt"])
            st.markdown("**Saved answer**")
            st.markdown(row["response"])
    st.subheader("Quiz results")
    if quizzes:
        for q in quizzes:
            st.write(f"{q['created_at']} — {q['subject']} / {q['topic']}: **{q['score']}/{q['total']}**")
    else:
        st.info("Quiz results abhi nahi hain.")

# -------------------- PROFILE --------------------
elif page == "My Profile":
    st.title("👤 My Profile")
    st.write("Ye basic local profile hai. Is starter app mein account password/login system abhi included nahi hai.")
    current = get_profile()
    with st.form("profile_form"):
        name = st.text_input("Your name", value=current["name"])
        class_name = st.text_input("Class / Course", value=current["class_name"])
        goal = st.text_area("Learning goal", value=current["goal"], placeholder="Example: Improve Python and Data Structures")
        saved = st.form_submit_button("Save profile", type="primary")
    if saved:
        save_profile(name, class_name, goal)
        st.success("Profile saved on this computer.")
        st.rerun()
    with get_conn() as conn:
        quiz_rows = conn.execute("SELECT subject, SUM(score) AS score, SUM(total) AS total FROM quiz_results GROUP BY subject").fetchall()
    st.subheader("Subject-wise quiz progress")
    if quiz_rows:
        for row in quiz_rows:
            pct = round(row["score"] * 100 / row["total"]) if row["total"] else 0
            st.write(f"**{row['subject']}** — {row['score']}/{row['total']} ({pct}%)")
            st.progress(pct / 100)
    else:
        st.info("Quiz complete karoge to subject-wise progress yahan show hoga.")

st.divider()
st.caption("StudyAI starter project • Data history is saved in studyai.db on this computer.")
