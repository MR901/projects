# builder_index.py – convert docs/ into FAISS index + pickle (vehicle domain)
import glob, pickle, re, yaml, pdfplumber
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss, numpy as np

EMBED = SentenceTransformer("all-MiniLM-L6-v2")
chunks, meta = [], []


def split(txt, size=350):
    return [txt[i : i + size] for i in range(0, len(txt), size)]


for file in glob.glob("docs/**/*", recursive=True):
    ext = Path(file).suffix.lower()
    if ext in {".md", ".txt"}:
        text = Path(file).read_text(encoding="utf-8")
    elif ext == ".pdf":
        text = "\n".join(p.extract_text() for p in pdfplumber.open(file).pages)
    else:
        continue

    front = Path(file).with_suffix(".yml")
    info = yaml.safe_load(front.read_text()) if front.exists() else {}

    for para in re.split(r"\n\s*\n", text):
        for block in split(para):
            if block.strip():
                chunks.append(block)
                meta.append(info)

    # Optionally append tag glossary once per file
    if "tags" in info:
        tag_doc = "\n".join(f"* **{k}** – {v}" for k, v in info["tags"].items())
        title = info.get("id") or info.get("model") or info.get("vehicle_type", "vehicle")
        chunks.append(f"Telemetry / tag glossary for {title}\n" + tag_doc)
        meta.append(info)

X = EMBED.encode(chunks, show_progress_bar=True, convert_to_numpy=True)
index = faiss.IndexFlatIP(X.shape[1])
index.add(X)

pickle.dump((index, chunks, meta), open("kb.pkl", "wb"))
print("✅ Vehicle KB built:", len(chunks), "chunks")


