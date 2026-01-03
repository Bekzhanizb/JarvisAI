from openai import OpenAI

from core.session import add, get
from core.config import OPENAI_API_KEY
from ai.prompt import SYSTEM_PROMPT
from storage.history_repo import save_message


client = OpenAI(api_key=OPENAI_API_KEY)




def chat(prompt: str) -> str:
    add("user", prompt)
    save_message("user", prompt)


    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get()


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )


    answer = response.choices[0].message.content


    add("assistant", answer)
    save_message("assistant", answer)


    return answer