import os, pickle, pdfplumber, numpy as np
from pathlib import Path
from tqdm import tqdm
import faiss
from sentence_transformers import SentenceTransformer

DOCS_DIR = Path("docs")
STORE_DIR = Path("store"); STORE_DIR.mkdir(exist_ok=True)
INDEX_PATH = STORE_DIR / "faiss.index"
META_PATH  = STORE_DIR / "meta.pkl"

EMB_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dims
CHUNK_SIZE = 900
CHUNK_OVERLAP = 200

def read_pdf(path: Path):
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, p in enumerate(pdf.pages, start=1):
            txt = p.extract_text() or ""
            pages.append((i, txt))
    return pages

def chunk_text(text, file, page, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    s = 0
    while s < len(text):
        e = min(len(text), s + size)
        chunk = text[s:e]
        if chunk.strip():
            chunks.append({
                "content": chunk,
                "source": file,
                "page": page
            })
        s += max(1, size - overlap)
    return chunks

def build_corpus():
    items = []
    for pdf in sorted(DOCS_DIR.glob("*.pdf")):
        for page_number, text in read_pdf(pdf):
            items += chunk_text(text, pdf.name, page_number)
    return items

def main():
    print("Cargando modelo de embeddings…")
    model = SentenceTransformer(EMB_NAME)
    corpus = build_corpus()
    if not corpus:
        raise SystemExit("No hay PDFs en docs/.")
    texts = [it["content"] for it in corpus]
    print(f"Generando embeddings de {len(texts)} fragmentos…")
    embs = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)  # producto interno ≈ coseno (normalizados)
    index.add(embs.astype("float32"))
    faiss.write_index(index, str(INDEX_PATH))
    with open(META_PATH, "wb") as f:
        pickle.dump(corpus, f)
    print(f"Listo. Guardado en {STORE_DIR}/ (n={len(texts)}).")

if __name__ == "__main__":
    main()
