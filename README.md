# lise-rag

Chatbot **RAG** (Retrieval-Augmented Generation) para responder **solo** con lo que dicen tus **PDFs** (por ejemplo, reglamentos y programas de curso), citando **(archivo, página)**. Construido con **Streamlit + FAISS + sentence-transformers** y compatible con Moodle vía **iframe**.

> Demo local: subir PDFs desde la barra lateral → **Re-indexar** → preguntar.  
> Despliegue recomendado: **Streamlit Cloud** (gratis) y embeber en Moodle.

---

## 🚀 Características
- ✅ Responde **solo** en base a tus documentos (con citas: *archivo, página*).
- ✅ **Uploader admin** para subir PDFs y **re-indexar** desde la app.
- ✅ Índice vectorial **FAISS** local (sin base de datos paga).
- ✅ Elegí LLM: **Gemini** (Google) u **OpenAI** (por variables de entorno).
- ✅ Fácil de embeber en **Moodle** con un `<iframe>`.

---

## 🧱 Estructura
```
lise-rag/
 ├─ app.py               # Chat con uploader admin + re-indexar
 ├─ ingest.py            # Indexación desde CLI (opcional)
 ├─ requirements.txt
 ├─ docs/                # Tus PDFs (colocar aquí o subir desde la app)
 ├─ store/               # Índice FAISS y metadatos (se genera solo)
 └─ .streamlit/
     └─ secrets.sample.toml   # Ejemplo de secrets para despliegue
```

> **Nota:** `store/` se ignora en Git; se crea en ejecución.

---

## 🖥️ Uso local

1) Crear/activar entorno e instalar dependencias
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

2) Configurar proveedor y clave (recomendado **Gemini**)
```bash
# macOS / Linux (solo esta sesión)
export LLM_PROVIDER=gemini
export GEMINI_API_KEY="TU_CLAVE"
export ADMIN_PASSWORD="cambia_esta_clave"

# Windows (PowerShell, persistente para tu usuario)
setx LLM_PROVIDER "gemini"
setx GEMINI_API_KEY "TU_CLAVE"
setx ADMIN_PASSWORD "cambia_esta_clave"
```

3) Ejecutar la app
```bash
streamlit run app.py
```
Abrí el enlace local. En la barra lateral **🔐 Admin**: subí PDFs → **Re-indexar** → preguntá.

> PDFs **escaneados**: pasales **OCR** (Drive → “Abrir con Documentos” → Descargar como PDF) para que tengan texto.

---

## ☁️ Despliegue en Streamlit Cloud (recomendado)
1) Subí este proyecto a un **repo de GitHub** (por ejemplo, `lise-rag`).  
2) En Streamlit Cloud → **New app** → elegí tu repo/branch.  
3) En **Settings → Secrets**, pegá:
```
LLM_PROVIDER = "gemini"
GEMINI_API_KEY = "TU_CLAVE"
ADMIN_PASSWORD = "CLAVE_ADMIN"
```
4) Deploy. Streamlit te da una **URL pública** (estable).

### Embeber en Moodle
Agregá un recurso **Página** o **Etiqueta**, botón `<>` (HTML) y pega:
```html
<iframe src="https://TU-APP.streamlit.app/?embedded=true"
        width="100%" height="720" style="border:0;"></iframe>
```
> Si tu Moodle bloquea iframes, usá un recurso **URL** para abrir en pestaña nueva.

---

## 🔄 Actualizar documentos
- **Desde la app**: barra lateral → subir PDFs → **Re-indexar**.
- **Por archivos**: copiá PDFs a `docs/` y corré `python ingest.py` (opcional).

---

## 🔐 Seguridad y buenas prácticas
- Protegé el uploader con `ADMIN_PASSWORD` (ya soportado).  
- No subas claves al repo. Usá **Secrets** en Streamlit Cloud o `.streamlit/secrets.toml` **localmente** (ver ejemplo).  
- Evitá exponer PDFs con información sensible si la app es pública.

---

## ⚙️ Variables de entorno
- `LLM_PROVIDER`: `gemini` | `openai`
- `GEMINI_API_KEY`: clave de Google AI Studio (si usás Gemini)
- `OPENAI_API_KEY`: clave de OpenAI (si usás OpenAI)
- `ADMIN_PASSWORD`: clave para habilitar el uploader admin

### Ejemplo `.streamlit/secrets.toml` (local)
Crea un archivo `.streamlit/secrets.toml` con:
```toml
LLM_PROVIDER = "gemini"
GEMINI_API_KEY = "TU_CLAVE"
ADMIN_PASSWORD = "CLAVE_ADMIN"
```

---

## 🧪 Troubleshooting
- **PowerShell bloquea activar el entorno** → Ejecutá:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\.venv\Scripts\Activate.ps1
  ```
- **No indexa nada** → Asegurate de que haya PDFs con **texto** (no solo imágenes).  
- **Respuestas sin citas** → Revisá que el prompt no haya sido modificado y que el índice exista en `store/`.

---

## 📝 Licencia
Este proyecto se distribuye bajo licencia **MIT** (ver `LICENSE`).

---

## 🙌 Créditos
- FAISS, sentence-transformers, Streamlit.
- Diseño de flujo RAG adaptado para cursos y Moodle.
