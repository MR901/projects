# app.py – Streamlit UI + Groq + RAG
import os, time, re
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
import markdown as md
from system_prompt import CENTRIFUGE_SYSTEM_PROMPT
from rag_support import fetch_context, guess_machine

# ── secrets ────────────────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
if not API_KEY:
    st.error("Add GROQ_API_KEY to .env or Streamlit Secrets"); st.stop()
client = Groq(api_key=API_KEY)
MODEL = "llama3-8b-8192"

# ── page css / banner ──────────────────────────────────────────────────────
st.set_page_config(page_title="🌀 Centrifuge Operations Support", page_icon="🌀")
st.markdown("""
<style>
body, textarea, input{font-family:'Inter',sans-serif}
header,footer{visibility:hidden}
div.stApp{background:radial-gradient(circle at 30% 30%,#f4f9ff 0%,#e6f0fd 45%,#f0f4fa 100%)}
.bubble{white-space:pre-wrap;padding:12px 16px;margin:4px 0;max-width:85%;
 border-radius:18px;line-height:1.45;box-shadow:0 2px 6px rgba(0,0,0,0.06);}
.user{align-self:flex-end;background:#1976d2;color:#fff;border-bottom-right-radius:4px}
.assistant{align-self:flex-start;background:#ffffffd8;border-bottom-left-radius:4px}
.assistant h2{font-size:1.05rem;margin:0.3rem 0 0.15rem;}
.assistant h3{font-size:0.95rem;margin:0.25rem 0;}
.assistant p{margin:0.35rem 0;}
.assistant ul{margin:0.3rem 0 0.3rem 1.2rem;}
.assistant table{border-collapse:collapse;width:100%;font-size:0.9rem;}
.assistant th,.assistant td{border:1px solid #ccc;padding:4px 6px;}
.cursor{display:inline-block;width:6px;height:15px;background:#444;
 animation:blink 1s steps(2,start) infinite}
@keyframes blink{to{visibility:hidden}}
</style>
""", unsafe_allow_html=True)
st.markdown("<h1 style='text-align:center;margin:-1rem 0 .2rem;color:#0b3c91'>🌀 Centrifuge Operations Support</h1>", unsafe_allow_html=True)

# ── session state ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    # ❶ SYSTEM prompt (hidden)
    st.session_state.messages = [
        {"role": "system", "content": CENTRIFUGE_SYSTEM_PROMPT},
        # ❷ Friendly greeting shown to the operator
        {
            "role": "assistant",
            "content": (
                "Hi — I’m **Dyna**, your centrifuge reliability engineer. "
                "Glad to be on shift with you. What centrifuge question can I tackle first?"
            ),
        },
    ]

# ── helper to render bubbles ──────────────────────────────────────────────
def bubble(role, md_text, stream=False):
    html = md.markdown(md_text, extensions=["nl2br","tables","fenced_code"])
    cursor = '<span class="cursor"></span>' if stream else ""
    css = "user" if role=="user" else "assistant"
    st.markdown(f'<div class="bubble {css}">{html}{cursor}</div>',
                unsafe_allow_html=True)

# replay history (skip sys prompt)
for m in st.session_state.messages[1:]:
    if m["role"] in ("assistant", "user"):   # ONLY show human-facing roles
        bubble(m["role"], m["content"])

# ── user input ────────────────────────────────────────────────────────────
prompt = st.chat_input("Type here to troubleshoot …")

if prompt:
    # show user
    st.session_state.messages.append({"role":"user","content":prompt})
    bubble("user", prompt)

    # RAG context
    context = fetch_context(prompt)
    st.session_state.messages.append({"role":"system","content":f"### Local context\n{context}"})

    # stream LLM
    placeholder = st.empty(); tokens=[]
    stream = client.chat.completions.create(
        model=MODEL, messages=st.session_state.messages, stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        tokens.append(delta)
        html = md.markdown("".join(tokens), extensions=["nl2br","tables","fenced_code"])
        placeholder.markdown(f'<div class="bubble assistant">{html}<span class="cursor"></span></div>', unsafe_allow_html=True)
        time.sleep(0.03)

    final = "".join(tokens)
    placeholder.markdown(f'<div class="bubble assistant">{md.markdown(final, extensions=["nl2br","tables","fenced_code"])}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role":"assistant","content":final})

# ── download chat (sidebar) ───────────────────────────────────────────────
if st.sidebar.button("📥 Download chat (.md)"):
    md_chat = []
    for m in st.session_state.messages[1:]:
        role = "**You:**" if m["role"]=="user" else "**Dyna:**"
        md_chat.append(f"{role}\n\n{m['content']}\n")
    st.sidebar.download_button("Save file", "\n---\n".join(md_chat),
                               file_name="centrifuge_chat.md",
                               mime="text/markdown")
