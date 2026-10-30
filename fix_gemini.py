
from pathlib import Path

path = Path("app.py")
code = path.read_text(encoding="utf-8")

start = code.find("def ask_ai(")
end = code.find("init_db()", start)

if start == -1 or end == -1:
    raise RuntimeError(
        "Code section nahi mila. app.py change nahi kiya."
    )

replacement = '''def ask_ai(prompt, model=None, image_bytes=None, system=None):
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
            + "\\n\\nStudent question: "
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


'''

path.write_text(
    code[:start] + replacement + code[end:],
    encoding="utf-8"
)

print("Gemini code updated successfully.")
