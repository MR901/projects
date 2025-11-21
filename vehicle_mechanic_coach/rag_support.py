# rag_support.py – fetch top-k context snippets for vehicle coaching
import re, pickle, numpy as np
from sentence_transformers import SentenceTransformer

INDEX, CHUNKS, META = pickle.load(open("kb.pkl", "rb"))
EMBED = SentenceTransformer("all-MiniLM-L6-v2")

# Simple vehicle ID / model regex heuristics
# Example IDs: CAR-001, BIKE-010, SCOOTER-005, TRUCK-020
ID_RE = re.compile(r"\b(?:CAR|BIKE|SCOOTER|TRUCK)-\d{2,4}\b", re.I)

# Very rough make/model pattern: brand name + displacement or engine size
MOD_RE = re.compile(
    r"\b("
    r"Maruti|Suzuki|Honda|Hyundai|Toyota|Tata|Mahindra|Kia|Skoda|Volkswagen|VW|Ford|"
    r"Royal\s+Enfield|Enfield|Bajaj|TVS|Hero|Yamaha|KTM"
    r")\b[^,\n]{0,40}\b("
    r"\d{2,4}cc|\d\.\dL|\dL"
    r")",
    re.I,
)


def fetch_context(query: str, k: int = 4) -> str:
    """Return concatenated KB snippets + their meta tags for the given query."""
    vec = EMBED.encode([query], convert_to_numpy=True)
    D, I = INDEX.search(vec, k)
    texts = []
    for idx in I[0]:
        info = META[idx] or {}
        tag = (
            info.get("id")
            or info.get("model")
            or info.get("vehicle_type")
            or "GENERIC"
        )
        texts.append(f"[{tag}] {CHUNKS[idx]}")
    return "\n\n".join(texts)


def guess_vehicle(query: str):
    """Best-effort guess of vehicle ID or make/model from the user query."""
    m = ID_RE.search(query)
    if m:
        return m.group().upper()
    m = MOD_RE.search(query)
    if m:
        return m.group(0)
    return None


