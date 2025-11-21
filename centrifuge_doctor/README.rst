===============================
Centrifuge Doctor – Ops Copilot
===============================

Overview
========

``centrifuge_doctor`` is a small, self‑contained Streamlit application that acts as
an operations copilot for edible‑oil centrifuges (Alfa Laval PX100 degumming and
Westfalia RS/RSB/RSE refinement machines).

It combines:

* a **retrieval‑augmented generation (RAG)** knowledge base built from your own
  operating notes and meta‑data in ``docs/``,
* a **Groq‑hosted LLM** (Llama 3) with a centrifuge‑specific system prompt, and
* a **chat UI** tuned for control‑room operators.

Typical questions it is designed for:

* "Vibration alarm on CF‑105 and bowl speed fluctuating – is this safe to keep running?"
* "Why do operators say I must do multiple large discharges to build back‑pressure?"
* "During my shift degumming throughput is lower than others – what might I be doing wrong?"


Problem Statement
=================

Front‑line operators often have to diagnose centrifuge issues in real time:

* rising **vibration**,
* marginal **bearing temperatures**,
* unexpected **back‑pressure** behaviour, and
* unclear **throughput losses**.

The relevant knowledge is usually scattered across OEM manuals, site‑specific
notes, and senior engineers' experience. The goal of this project is to:

* centralise that knowledge in a **queryable knowledge base**, and
* expose it through a **conversational assistant** that understands your machine
  IDs, tags, and operating context.


High‑Level Approach
===================

The project follows a standard RAG pattern with a thin, focused UI:

1. **Domain docs → KB index**

   * Each machine (for example, ``CF‑105``) has:

     * a meta file (e.g. ``cf-105-meta.yml``) containing model, manufacturer,
       typical limits and tag glossary, and
     * an operating‑notes file (e.g. ``cf-105-ops.md``) with alarm limits and
       troubleshooting tips.

   * ``builder_index.py`` scans ``docs/``, chunks the text, embeds it using
     ``SentenceTransformer("all-MiniLM-L6-v2")`` and stores:

     * a FAISS similarity index,
     * text chunks, and
     * associated meta‑data

     into a single pickle file, ``kb.pkl``.

2. **Query‑time retrieval**

   * ``rag_support.fetch_context`` loads ``kb.pkl``, embeds the user query and
     retrieves the top‑k most relevant snippets (with their machine IDs / tags).

3. **LLM reasoning with system prompt**

   * ``system_prompt.CENTRIFUGE_SYSTEM_PROMPT`` defines the persona (Dyna),
     core facts (machines in scope, alarm limits, sensors), and a strict response
     style (clear, concise, safety‑aware Markdown).
   * ``app.py`` passes both the system prompt and retrieved context into Groq's
     Llama 3 chat completion API.

4. **Operator‑friendly UI**

   * ``app.py`` implements a Streamlit chat interface with speech‑bubble styling,
     streaming tokens, and a sidebar button to download the chat as
     ``centrifuge_chat.md``.


Repository Layout
=================

The important pieces in this folder are:

* ``app.py`` – Streamlit UI + Groq client + RAG glue code.
* ``rag_support.py`` – loads ``kb.pkl`` and exposes:

  * ``fetch_context(query: str, k: int = 4)`` – return concatenated snippets
    with machine IDs, and
  * ``guess_machine(query: str)`` – simple regex‑based guess of machine ID/model.

* ``system_prompt.py`` – contains the ``CENTRIFUGE_SYSTEM_PROMPT`` string used as
  the system message for all Groq calls.
* ``builder_index.py`` – one‑off (or periodic) script to rebuild ``kb.pkl`` from
  the markdown/YAML/PDF content in ``docs/``.
* ``docs/`` – source of truth for the knowledge base; contains:

  * ``*-meta.yml`` files (per‑centrifuge meta‑data and tag glossary),
  * ``*-ops.md`` files (operating notes, alarm tables, troubleshooting tips).

* ``kb.pkl`` – the compiled FAISS index + chunks + meta‑data used at runtime.
* ``requirements.txt`` – Python dependencies for this mini‑project.


How It Works at Runtime
=======================

1. The operator opens the Streamlit app and asks a question in the chat box.
2. ``app.py``:

   * appends the user message to the chat history,
   * calls ``fetch_context`` to bring in the most relevant KB snippets, and
   * injects that context as a hidden system message.

3. The app then streams a Groq chat completion (Llama 3) with:

   * the centrifuge‑specific system prompt,
   * the accumulated conversation history, and
   * the local context from the KB.

4. The answer is rendered as an assistant "bubble" and also stored in
   ``st.session_state.messages`` so the conversation persists across turns.
5. At any time the operator can download the chat as a Markdown file via the
   sidebar.


Setup and Installation
======================

1. **Create and activate a virtual environment** (recommended)::

   cd /home/mohit/Documents/new_age/website-MR901.CO.IN/projects/centrifuge_doctor
   python -m venv .venv
   source .venv/bin/activate

2. **Install dependencies**::

   pip install -r requirements.txt

3. **Configure Groq API key**

   The app expects a ``GROQ_API_KEY`` either:

   * in a local ``.env`` file in this directory::

       GROQ_API_KEY=sk_...

   * or in Streamlit secrets (when deployed).


Building / Updating the Knowledge Base
======================================

When you change anything in ``docs/`` (add a new centrifuge, adjust limits, add
more operating notes), you should regenerate ``kb.pkl``.

From the ``centrifuge_doctor`` folder run::

   python builder_index.py

This will:

* scan all supported files under ``docs/`` (``.md``, ``.txt``, ``.pdf``),
* build embeddings and a FAISS index, and
* overwrite ``kb.pkl`` with the new index.


Running the App
===============

With your virtual environment activated and ``kb.pkl`` present, start the app::

   streamlit run app.py

Then open the URL printed in the terminal (typically
``http://localhost:8501``) in your browser.


Example Interactions
====================

Some example prompts to try:

* "On CF‑105 the vibration alarm keeps flickering at 5–6 mm/s during neutralisation –
  what should I check first?"
* "Degumming throughput on my shift is consistently lower than others – what operating
  mistakes should I look for?"
* "Slip speed tag shows 1 every cycle and I'm also seeing a vibration alarm – is this
  acceptable or a sign of a deeper issue?"


Limitations and Next Steps
==========================

* The assistant only knows what is encoded in ``docs/`` and the system prompt – it is
  **not** connected to live plant data.
* It assumes the machines are similar to the PX100 and Westfalia RS/RSB/RSE separators
  described in the meta files.

Ideas for extension:

* Pulling in **live tag values** (vibration, RPM, bearing temperatures) from your
  historian for richer diagnostics.
* Adding more **site‑specific SOPs** and incident post‑mortems into ``docs/`` to
  improve recommendations.
* Deploying the Streamlit app behind SSO for production use in the control room.


