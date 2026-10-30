
from pathlib import Path

path = Path("app.py")
code = path.read_text(encoding="utf-8")

start = code.index("def ask_ai(")
end = code.index("init_db()", start)

replacement = '''def ask_ai(prompt, model=None, image_bytes=None, system=None):
    import base64

    messages = [{
        "role": "system",
        "content": system or (
            "You are StudyAI, a helpful college tutor. "
            "Answer the exact question in clear, simple English. "
            "Use correct definitions and examples. "
            "Never produce random or broken text."
        )
    }]

    if image_bytes:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        user_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {
                "url": "data:image/jpeg;base64," + encoded
            }}
        ]
    else:
        user_content = prompt

    messages.append({"role": "user", "content": user_content})

    try:
        models = client.models.list().data
        if not models:
            return "Error: LM Studio mein model load karke server start karo."

        model_id = next(
            (m.id for m in models
             if "qwen2.5-vl-3b-instruct" in m.id.lower()),
            None
        )

        if not model_id:
            return "Error: Qwen model LM Studio server mein nahi mila."

        result = client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0.2,
            max_tokens=700
        )

        answer = result.choices[0].message.content
        if isinstance(answer, list):
            answer = " ".join(
                item.get("text", "")
                for item in answer if isinstance(item, dict)
            )

        return answer.strip() if answer else "Model ne empty answer diya."

    except Exception as e:
        return f"AI connection error: {e}"


def check_ollama():
    try:
        models = client.models.list().data
        if not models:
            return False, "LM Studio mein model load nahi hai."
        return True, ""
    except Exception as e:
        return False, str(e)


'''

code = code[:start] + replacement + code[end:]
path.write_text(code, encoding="utf-8")
print("AI code updated successfully.")
