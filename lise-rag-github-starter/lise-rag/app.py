import os, pickle, io, faiss, numpy as np, streamlit as st
from sentence_transformers import SentenceTransformer
import pdfplumber

# --- Configuración ---
INDEX_PATH = "store/faiss.index"
META_PATH  = "store/meta.pkl"
DOCS_DIR   = "docs"
STORE_DIR  = "store"
EMB_NAME   = "sentence-transformers/all-MiniLM-L6-v2"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# --- Utilidades de embeddings e índice ---
def read_pdf(path):
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, p in enumerate(pdf.pages, start=1):
            txt = p.extract_text() or ""
            pages.append((i, txt))
    return pages

def chunk_text(text, file, page, size=900, overlap=200):
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
    for name in sorted(os.listdir(DOCS_DIR)):
        if not name.lower().endswith(".pdf"):
            continue
        path = os.path.join(DOCS_DIR, name)
        for page_number, text in read_pdf(path):
            items += chunk_text(text, name, page_number)
    return items

def build_index():
    os.makedirs(STORE_DIR, exist_ok=True)
    model = SentenceTransformer(EMB_NAME)
    corpus = build_corpus()
    if not corpus:
        return False, "No hay PDFs en docs/."
    texts = [it["content"] for it in corpus]
    embs = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embs.astype("float32"))
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(corpus, f)
    return True, f"Índice creado: {len(texts)} fragmentos."

@st.cache_resource(show_spinner=False)
def load_search():
    index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, "rb") as f:
        meta = pickle.load(f)
    emb_model = SentenceTransformer(EMB_NAME)
    return index, meta, emb_model

def retrieve(query, k=4):
    index, meta, emb_model = load_search()
    q = emb_model.encode([query], normalize_embeddings=True).astype("float32")
    D, I = index.search(q, k)
    hits = []
    for idx, score in zip(I[0], D[0]):
        if idx == -1: continue
        item = dict(meta[idx])
        item["score"] = float(score)
        hits.append(item)
    return hits

def llm_answer(prompt):
    if LLM_PROVIDER == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        out = model.generate_content(prompt)
        return out.text
    elif LLM_PROVIDER == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":prompt}])
        return res.choices[0].message.content
    else:
        raise RuntimeError("Configura LLM_PROVIDER = gemini | openai")

def build_prompt(user_q, hits):
    context_blocks = []
    for h in hits:
        src = f"{h['source']} (p. {h['page']})"
        context_blocks.append(f"[{src}]\n{h['content']}")
    context = "\n\n---\n\n".join(context_blocks) if context_blocks else "(sin fragmentos)"
    rules = (
        "Eres un asistente para estudiantes. "
        "Responde SOLO con la información de los extractos 'Contexto'. "
        "Cita entre paréntesis la fuente y página, por ejemplo (Reglamento.pdf, p. 3). "
        "Si no está en el contexto, responde: 'No aparece en los documentos proporcionados'."
    )
    return f"{rules}\n\nContexto:\n{context}\n\nPregunta: {user_q}\nRespuesta (en español, breve y precisa):"

# --- UI ---
st.set_page_config(page_title="Lise (RAG por PDFs)", page_icon="📚")
st.title("📚 Lise – Chat con tus PDFs")

# Quick status cards
col1, col2 = st.columns(2)
with col1:
    st.caption("📦 Carpeta de documentos: `docs/`")
with col2:
    st.caption("🗄️ Índice FAISS: `store/`")

# Admin uploader (opcional)
with st.sidebar:
    st.header("🔐 Admin")
    if ADMIN_PASSWORD:
        pw = st.text_input("Clave de admin", type="password")
        st.session_state.admin_ok = (pw == ADMIN_PASSWORD)
    else:
        st.info("Define ADMIN_PASSWORD en variables de entorno para proteger el uploader.")
        st.session_state.admin_ok = True

    if st.session_state.admin_ok:
        st.subheader("Agregar PDFs")
        up = st.file_uploader("Subí uno o más PDFs", type=["pdf"], accept_multiple_files=True)
        if st.button("Guardar en docs/"):
            if not up:
                st.warning("No seleccionaste archivos.")
            else:
                os.makedirs(DOCS_DIR, exist_ok=True)
                for uf in up:
                    with open(os.path.join(DOCS_DIR, uf.name), "wb") as f:
                        f.write(uf.read())
                st.success(f"Guardados {len(up)} archivo(s) en docs/.")

        if st.button("Re-indexar ahora"):
            with st.spinner("Construyendo índice…"):
                ok, msg = build_index()
                if ok:
                    load_search.clear()  # refrescar el recurso cacheado
                    st.success(msg)
                else:
                    st.error(msg)

# Estado inicial
if not (os.path.exists(INDEX_PATH) and os.path.exists(META_PATH)):
    st.warning("No hay índice. Subí PDFs (en la barra lateral) o ponelos en docs/ y re-indexá.")
else:
    if "history" not in st.session_state:
        st.session_state.history = []

    for role, text in st.session_state.history:
        with st.chat_message(role):
            st.markdown(text)

    q = st.chat_input("Preguntá sobre los reglamentos…")
    if q:
        with st.chat_message("user"):
            st.markdown(q)
        hits = retrieve(q, k=4)
        prompt = build_prompt(q, hits)
        with st.spinner("Pensando…"):
            ans = llm_answer(prompt)
        with st.chat_message("assistant"):
            st.markdown(ans)
            with st.expander("Ver fragmentos citados"):
                for h in hits:
                    st.markdown(f"**{h['source']} – p. {h['page']}** (score {h['score']:.3f})")
                    st.write(h["content"])
        st.session_state.history.append(("user", q))
        st.session_state.history.append(("assistant", ans))
