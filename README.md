# PDF Question‑Answering Agent

A Streamlit web app that lets you upload PDF documents, stores them in Astra DB as vector embeddings using LangChain, and then ask natural‑language questions answered using OpenAI’s gpt‑4o model over your own documents.

## Requirements

- Python 3.9+  
- Install dependencies:

```bash
pip install -r requirements.txt
```

Main libraries: Streamlit, LangChain (`langchain`, `langchain-openai`, `langchain-astradb`, `langchainhub`), `pypdf`, `python-dotenv`.

## Environment variables

Create a `.env` file in the project root for local development:

```bash
OPENAI_API_KEY=your_openai_key_here
ASTRADB_API_ENDPOINT=your_astra_endpoint_here
ASTRADB_APPLICATION_TOKEN=your_astra_token_here
```

- The app loads these with `python-dotenv` (`load_dotenv()`), then accesses them via `os.getenv(...)`.  
- For deployment (Render/Fly/Railway/etc.), **do not upload `.env`**; instead, set the same variable names in the platform’s “Environment / Secrets” settings.

## Running locally

1. Clone the repository and install requirements:

   ```bash
   pip install -r requirements.txt
   ```

2. Create `.env` as shown above with your OpenAI and Astra DB credentials.

3. Start the app:

   ```bash
   streamlit run app.py
   ```

4. Open the URL Streamlit prints in the terminal (usually `http://localhost:8501`).

## Quick usage

- **Set user id:** At the top, enter a user id (default is `user123`) to isolate documents per user.  
- **Upload PDFs:** Use the “Upload” section to upload a PDF; it is split into text chunks, embedded, and stored in Astra DB for that user.  
- **Manage files:** The “My files” list shows stored PDFs for the current user; you can delete individual files or clear all docs.  
- **Ask questions:** In “Ask about your documents”, type a question and press **Ask**; the app retrieves relevant chunks from Astra and uses OpenAI (via LangChain) to generate an answer plus expandable source snippets.

## Deploying

On a hosting platform (e.g. Render, Fly.io, Railway):

- Push this project to a Git repository (for example on GitHub) and create a new **web service** from that repo in your hosting platform’s dashboard.
- In the service’s Environment / Secrets settings, add the variables `OPENAI_API_KEY`, `ASTRADB_API_ENDPOINT`, `ASTRADB_APPLICATION_TOKEN` with the same values you used locally.
- Use a start command like:

  ```bash
  streamlit run app.py --server.port 8501 --server.address 0.0.0.0
  ```