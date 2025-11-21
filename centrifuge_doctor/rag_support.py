# rag_support.py – fetch top-k context snippets
import re, pickle, numpy as np
from sentence_transformers import SentenceTransformer

INDEX, CHUNKS, META = pickle.load(open("kb.pkl", "rb"))
EMBED = SentenceTransformer("all-MiniLM-L6-v2")

# simple ID / model regex
ID_RE  = re.compile(r"CF-\d{3,4}", re.I)
MOD_RE = re.compile(r"\b(PX ?\d+|RSB?\d+|RSE\d+)\b", re.I)

def fetch_context(query: str, k=4):
    """Return concatenated snippets + their meta tags."""
    vec = EMBED.encode([query], convert_to_numpy=True)
    D, I = INDEX.search(vec, k)
    texts = []
    for idx in I[0]:
        tag = META[idx].get("id") or META[idx].get("model", "UNK")
        texts.append(f"[{tag}] {CHUNKS[idx]}")
    return "\n\n".join(texts)

def guess_machine(query: str):
    if ID_RE.search(query):   return ID_RE.search(query).group().upper()
    if MOD_RE.search(query):  return MOD_RE.search(query).group().upper()
    return None
