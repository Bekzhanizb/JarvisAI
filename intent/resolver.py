import json
from openai import OpenAI

client = OpenAI()


def load_apps():
    with open("core/app_scanner/app_index.json", encoding="utf-8") as f:
        return json.load(f)


def resolve_intent(user_text):
    apps = load_apps()

    system_prompt = """
Сен Linux жүйесінде жұмыс істейтін ассистентсің.
Пайдаланушы қосымшаны ашуды сұрайды.

Сенің мақсатың:
1. Қандай қосымшаны ашқысы келетінін түсіну
2. Төмендегі тізімнен ЕҢ СӘЙКЕС қосымшаны таңдау
3. Қосымшаның exec командасын қайтару

Егер сенімді болмасаң — ең жақын сәйкесін таңда.
Тек JSON қайтар.
"""

    user_prompt = f"""
Пайдаланушының сөзі:
"{user_text}"

Қосымшалар тізімі:
{json.dumps(apps, ensure_ascii=False)}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    content = response.choices[0].message.content
    return json.loads(content)
