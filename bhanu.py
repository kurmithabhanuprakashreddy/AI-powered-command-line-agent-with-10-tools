#!/usr/bin/env python3
# bhanu.py — A simple terminal AI agent with tools
# Works offline with a basic chat fallback. Optionally uses OpenAI or Ollama if available.

import os
import sys
import time
import json
import math
import random
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+
import requests

BANNER = r"""
██████  ██   ██  █████  ███    ██ ██    ██ 
██   ██ ██   ██ ██   ██ ████   ██ ██    ██ 
██████  ███████ ███████ ██ ██  ██ ██    ██ 
██   ██ ██   ██ ██   ██ ██  ██ ██ ██    ██ 
██████  ██   ██ ██   ██ ██   ████  ██████  
"""

HELP_TEXT = """
Tools you can use:
  • calc <expr>            -> evaluate math (e.g., "calc (12+8)*5")
  • weather <city>         -> quick weather
  • time [Zone/Name]       -> current time
  • joke                   -> random joke
  • quote                  -> motivational quote
  • dict <word>            -> dictionary meaning
  • translate <lang> <txt> -> translate text
  • news                   -> latest headlines
  • ip                     -> your public IP
  • todo [add/list/clear]  -> manage simple todo
  • help                   -> show this help
  • exit / quit            -> leave the chat
"""

# ----------------------------
# Tool: Calculator
# ----------------------------
def tool_calc(expr: str) -> str:
    allowed_names = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed_names.update({"__builtins__": {}})
    try:
        result = eval(expr, allowed_names, {})
        return f"{result}"
    except Exception as e:
        return f"Calc error: {e}"

# ----------------------------
# Tool: Weather (wttr.in)
# ----------------------------
def tool_weather(city: str) -> str:
    city = city.strip()
    if not city:
        return "Please provide a city, e.g., 'weather Hyderabad'."
    try:
        url = f"https://wttr.in/{city}?format=3"
        r = requests.get(url, timeout=6)
        if r.status_code == 200 and r.text.strip():
            return r.text.strip()
        return f"Couldn't fetch weather for '{city}'."
    except Exception:
        return f"The weather in {city} is sunny (dummy)."

# ----------------------------
# Tool: Time (local or TZ)
# ----------------------------
def tool_time(tz: str | None) -> str:
    try:
        if tz:
            now = datetime.now(ZoneInfo(tz.strip()))
            return now.strftime(f"%Y-%m-%d %H:%M:%S %Z (tz='{tz.strip()}')")
        else:
            now = datetime.now()
            return now.strftime("%Y-%m-%d %H:%M:%S (local)")
    except Exception as e:
        return f"Time error: {e}. Try e.g. 'time Asia/Kolkata'."

# ----------------------------
# Tool: Joke
# ----------------------------
def tool_joke() -> str:
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
        "Debugging: being the detective in a crime movie where you are also the murderer.",
    ]
    return random.choice(jokes)

# ----------------------------
# Tool: Quote
# ----------------------------
def tool_quote() -> str:
    quotes = [
        "Believe you can and you're halfway there.",
        "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "Do what you can, with what you have, where you are.",
    ]
    return random.choice(quotes)

# ----------------------------
# Tool: Dictionary (Free API)
# ----------------------------
def tool_dict(word: str) -> str:
    if not word:
        return "Usage: dict <word>"
    try:
        r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=6)
        if r.status_code == 200:
            j = r.json()
            meaning = j[0]["meanings"][0]["definitions"][0]["definition"]
            return f"{word}: {meaning}"
        return f"No definition found for {word}."
    except Exception:
        return f"{word}: meaning not found (offline)."

# ----------------------------
# Tool: Translate (LibreTranslate)
# ----------------------------
def tool_translate(lang: str, text: str) -> str:
    if not lang or not text:
        return "Usage: translate <lang> <text>"
    try:
        url = "https://libretranslate.de/translate"
        payload = {"q": text, "source": "en", "target": lang, "format": "text"}
        r = requests.post(url, data=payload, timeout=8)
        if r.status_code == 200:
            return r.json().get("translatedText", "Translation failed")
        return "Translation error."
    except Exception:
        return f"Translation (offline dummy): {text} in {lang}"

# ----------------------------
# Tool: News (NewsAPI-free demo or dummy)
# ----------------------------
def tool_news() -> str:
    try:
        r = requests.get("https://newsapi.org/v2/top-headlines?country=us&apiKey=demo", timeout=8)
        if r.status_code == 200:
            j = r.json()
            headlines = [a["title"] for a in j.get("articles", [])[:5]]
            return " | ".join(headlines) if headlines else "No news found."
    except Exception:
        pass
    return "Breaking news (offline dummy): AI agent Bhanu is getting smarter!"

# ----------------------------
# Tool: IP
# ----------------------------
def tool_ip() -> str:
    try:
        r = requests.get("https://api.ipify.org?format=json", timeout=5)
        if r.status_code == 200:
            return "Your IP: " + r.json()["ip"]
    except Exception:
        return "Your IP: 127.0.0.1 (dummy offline)"
    return "Could not fetch IP."

# ----------------------------
# Tool: Todo Manager
# ----------------------------
TODO_FILE = "bhanu_todo.json"

def load_todos():
    if os.path.exists(TODO_FILE):
        try:
            return json.load(open(TODO_FILE))
        except:
            return []
    return []

def save_todos(todos):
    with open(TODO_FILE, "w") as f:
        json.dump(todos, f)

def tool_todo(cmd: str) -> str:
    todos = load_todos()
    parts = cmd.split(maxsplit=2)
    if len(parts) == 1 or parts[1] == "list":
        return "Your TODOs:\n" + "\n".join([f"- {t}" for t in todos]) if todos else "No tasks yet."
    elif parts[1] == "add" and len(parts) > 2:
        todos.append(parts[2])
        save_todos(todos)
        return f"Added: {parts[2]}"
    elif parts[1] == "clear":
        save_todos([])
        return "Todo list cleared."
    else:
        return "Usage: todo add <task> | todo list | todo clear"

# ----------------------------
# Chat backends (unchanged from your code)
# ----------------------------
def chat_openai(messages: list[dict]) -> str | None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None

def chat_ollama(messages: list[dict]) -> str | None:
    try:
        def to_prompt(msgs):
            lines = []
            for m in msgs:
                role = m.get("role", "")
                content = m.get("content", "")
                if role == "user":
                    lines.append(f"User: {content}")
                elif role == "assistant":
                    lines.append(f"Assistant: {content}")
            lines.append("Assistant:")
            return "\n".join(lines)

        prompt = to_prompt(messages)
        data = {"model": "llama3.1", "prompt": prompt, "stream": False}
        r = requests.post("http://localhost:11434/api/generate", json=data, timeout=30)
        if r.status_code == 200:
            j = r.json()
            return j.get("response", "").strip()
        return None
    except Exception:
        return None

def chat_fallback(user_text: str) -> str:
    text = user_text.lower().strip()
    if any(k in text for k in ["hello", "hi", "hey", "namaste"]):
        return "Hi! I’m Bhanu — your terminal agent. Ask me to calc, check weather, or just chat!"
    if "binary search" in text:
        return "Binary search halves the search range in a sorted array; O(log n) time."
    if "linux tip" in text:
        return "Linux tip: use `ctrl+r` in the terminal to reverse-search your command history."
    if "sports" in text and "study" in text:
        return "Balance idea: 50-minute study sprints + 10-minute stretch or light drills."
    return "I’m offline 😅 — try a tool (calc/weather/time/joke/news/etc)."

# ----------------------------
# Agent loop
# ----------------------------
def print_banner():
    print(BANNER)
    print("Bhanu Terminal Agent — Tools + Chat\n")
    print(HELP_TEXT)

def handle_tool(user_input: str) -> str | None:
    s = user_input.strip()
    if s.lower() in ("help", "/help", "?"):
        return HELP_TEXT
    if s.lower() in ("exit", "quit"):
        return "__EXIT__"

    # calc
    if s.lower().startswith("calc "):
        return f"[calc] {tool_calc(s[5:].strip())}"

    # weather
    if s.lower().startswith("weather "):
        return f"[weather] {tool_weather(s[8:].strip())}"

    # time
    if s.lower().startswith("time"):
        rest = s[4:].strip()
        return f"[time] {tool_time(rest if rest else None)}"

    # joke
    if s.lower() == "joke":
        return f"[joke] {tool_joke()}"

    # quote
    if s.lower() == "quote":
        return f"[quote] {tool_quote()}"

    # dict
    if s.lower().startswith("dict "):
        return f"[dict] {tool_dict(s[5:].strip())}"

    # translate
    if s.lower().startswith("translate "):
        parts = s.split(maxsplit=2)
        if len(parts) >= 3:
            return f"[translate] {tool_translate(parts[1], parts[2])}"
        return "Usage: translate <lang> <text>"

    # news
    if s.lower() == "news":
        return f"[news] {tool_news()}"

    # ip
    if s.lower() == "ip":
        return f"[ip] {tool_ip()}"

    # todo
    if s.lower().startswith("todo"):
        return f"[todo] {tool_todo(s)}"

    return None

def main():
    print_banner()
    messages = [{"role": "system", "content": "You are Bhanu, a helpful, concise terminal AI agent."}]

    while True:
        try:
            user = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user:
            continue

        tool_reply = handle_tool(user)
        if tool_reply is not None:
            if tool_reply == "__EXIT__":
                print("Agent: Bye! 👋")
                break
            print(f"Agent: {tool_reply}")
            continue

        messages.append({"role": "user", "content": user})
        reply = chat_openai(messages) or chat_ollama(messages) or chat_fallback(user)
        messages.append({"role": "assistant", "content": reply})
        print(f"Agent: {reply}")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("Fatal error:\n", traceback.format_exc())
        sys.exit(1)
