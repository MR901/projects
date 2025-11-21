====================================
Vehicle Mechanic & Driving Coach App
====================================

Overview
========

``vehicle_mechanic_coach`` is a small Streamlit application that acts as a
digital **mechanic + driver/rider coach** for everyday ICE vehicles:
cars, motorcycles, scooters and light/medium trucks.

It combines:

* a **retrieval-augmented generation (RAG)** knowledge base built from your own
  vehicle notes and cheat-sheets in ``docs/``,
* a **Groq-hosted LLM** (Llama 3) with a vehicle-specific expert prompt, and
* a **chat UI** tuned for normal drivers/riders rather than engineers.

Example questions it is designed for:

* "My 1.2L petrol hatch is jerky in 1st gear in traffic – what am I doing wrong?"
* "150cc bike chain is noisy and the bike feels snappy on/off throttle."
* "Coolant temp climbs in city traffic with A/C on – is it safe to keep driving?"


High-Level Idea
===============

Most drivers and riders experience:

* strange **noises, vibrations or smells**,
* worrying **warning lights or temperature readings**, and
* uncertainty around **best driving/riding habits**.

The knowledge to diagnose and coach is usually held by a good local mechanic
or instructor. This project turns that experience into a **digital avatar**
that can:

* reason from your descriptions of symptoms and conditions, and
* give friendly, structured, safety-aware guidance.


Architecture
============

The project follows a simple RAG pattern:

1. **Docs → KB index**

   * Each vehicle archetype (e.g. small city petrol hatch, 150cc commuter bike)
     has:

     * a meta file (``*-meta.yml``) describing the vehicle, its key limits and
       telemetry-style tags, and
     * an ops file (``*-ops.md``) with operating notes, common complaints and
       best-practice guidance.

   * ``builder_index.py`` scans ``docs/``, chunks the text, embeds it with
     ``SentenceTransformer("all-MiniLM-L6-v2")`` and stores:

     * a FAISS similarity index,
     * text chunks, and
     * their meta-data

     as a single ``kb.pkl`` file.

2. **Query-time retrieval**

   * ``rag_support.fetch_context`` loads ``kb.pkl``, embeds the user query and
     retrieves the top-k relevant snippets, prepended with their IDs or models.

3. **LLM reasoning with expert system prompt**

   * ``system_prompt.VEHICLE_SYSTEM_PROMPT`` defines the persona (**Apex**, a
     master mechanic + driving coach) and the response flow (triage → diagnosis
     → actions → coaching).

   * ``app.py`` sends the system prompt, conversation history and retrieved
     context to Groq's Llama 3 chat completions API.

4. **Operator-friendly UI**

   * ``app.py`` implements a Streamlit chat interface with speech bubbles,
     streaming tokens and a sidebar button to download the chat as
     ``vehicle_chat.md``.


Key Files
=========

* ``app.py`` – Streamlit UI + Groq client + glue to RAG and system prompt.
* ``system_prompt.py`` – defines ``VEHICLE_SYSTEM_PROMPT``, the expert persona.
* ``rag_support.py`` – loads ``kb.pkl`` and exposes:

  * ``fetch_context(query: str, k: int = 4)`` – get concatenated snippets, and
  * ``guess_vehicle(query: str)`` – best-effort guess of vehicle ID or make/model.

* ``builder_index.py`` – one-off or periodic script to rebuild ``kb.pkl`` from
  the markdown/YAML/PDF content in ``docs/``.
* ``docs/`` – domain knowledge source:

  * ``car-city-petrol-hatch-meta.yml`` / ``car-city-petrol-hatch-ops.md``
  * ``bike-150cc-commuter-meta.yml`` / ``bike-150cc-commuter-ops.md``

  You can add more vehicle archetypes by following the same pattern.

* ``requirements.txt`` – Python dependencies.


Setup
=====

1. **Create and activate a virtual environment** (recommended)::

   cd /home/mohit/Documents/new_age/website-MR901.CO.IN/projects/vehicle_mechanic_coach
   python -m venv .venv
   source .venv/bin/activate

2. **Install dependencies**::

   pip install -r requirements.txt

3. **Configure Groq API key**

   Create a local ``.env`` file in this directory (or use Streamlit secrets)::

     GROQ_API_KEY=sk_...


Building / Updating the Knowledge Base
======================================

When you change anything in ``docs/`` (add vehicles, tweak notes, add best
practice sections), regenerate ``kb.pkl``::

   python builder_index.py

This scans supported files under ``docs/`` (``.md``, ``.txt``, ``.pdf``) and
rebuilds the FAISS index + chunks + meta-data.


Running the App
===============

With your virtual environment active and ``kb.pkl`` built, start the app::

   streamlit run app.py

Then open the URL shown in the terminal (typically
``http://localhost:8501``) in your browser.


Next Steps
==========

* Add more vehicle profiles (diesel sedans, scooters, loaded trucks, hills
  driving, etc.) by creating new ``*-meta.yml`` + ``*-ops.md`` pairs.
* Enrich the ops files with real-world complaints and coaching advice from your
  own experience.
* Optionally connect this to real OBD or telematics data in the future for
  live, data-driven advice.


