import os
import time
import tempfile

from dotenv import load_dotenv
import streamlit as st
from rag_backend import (
    rag_answer,
    upload_pdf_to_astra,
    delete_user_docs,
    list_user_sources,
    delete_user_file,
)

def uploader_not_empty(uploaded):
    return uploaded is not None

if "uploaded_to_astra" not in st.session_state:
    st.session_state["uploaded_to_astra"] = {}


load_dotenv()
st.set_page_config(page_title="My PDF's agent", layout="centered")
st.markdown("""
<style>
/* Base text size */
html, body, [class*="css"] {
    font-size: 18px;
}

/* Make content area wider */
.block-container {
    max-width: 1100px;
}

/* Title and section headers */
h1 {
    font-size: 2.6rem;
    text-align: center;
    margin-bottom: 2.5rem;
}
            
/* Extra space between title and first text input */
div[data-testid="stTextInput"] {
    margin-top: 2.5rem;
}
            


/* Labels and captions */
label, .stCaption {
    font-size: 1.2rem !important;
}

/* Special label for the question */
.big-question-label {
    font-size: 1.8rem !important;
    font-weight: 600;
    margin-top: 2rem;
    margin-bottom: 0.6rem;
    text-align: center;
}
.user-id-block {
    margin-top: 3rem;
}

            
.clear-docs-block {
    margin-top: 3rem;
}
/* Text inputs */
div[data-testid="stTextInput"] input {
    font-size: 1.0rem !important;
}

/* Buttons */
div.stButton > button {
    font-size: 1.0rem !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
.wide-warning div.stAlert {
    width: 260px;   /* try 260–320 */
}
</style>
""", unsafe_allow_html=True)


st.title("My document's agent")

col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
with col1:
        st.markdown('<div class="user-id-block">', unsafe_allow_html=True)
        user_id = st.text_input("User id", value="user123")
        st.markdown('</div>', unsafe_allow_html=True)



left_col, right_col = st.columns([1.4, 1], gap="large")

with left_col:
    st.subheader("Upload")
    uploaded = st.file_uploader("Upload a PDF", type="pdf")

    if uploaded is not None:
        fname = uploaded.name
        already = st.session_state["uploaded_to_astra"].get(fname, False)

        if not already:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded.getbuffer())
                temp_path = tmp.name

            start = time.perf_counter()
            n_docs = upload_pdf_to_astra(
                temp_path,
                user_id=user_id,
                display_name=fname
            )
            upload_secs = time.perf_counter() - start
            st.caption(f"Upload took {upload_secs:.2f}s")

            if n_docs > 0:
                st.success(f"Uploaded {n_docs} chunks to Astra.")
            else:
                st.warning("This PDF had no readable text to index.")

            try:
                os.remove(temp_path)
            except OSError:
                pass

            st.session_state["uploaded_to_astra"][fname] = True
with col2:
    st.markdown('<div style="margin-top: 1.5rem;">', unsafe_allow_html=True)
    if st.button("Clear docs"):
        if uploader_not_empty(uploaded):
            st.warning("Please empty the uploader first (click X).")
        elif not user_id:
            st.error("Please enter a user id first.")
        else:
            deleted = delete_user_docs(user_id)
            st.success(f"Deleted {deleted} documents for user '{user_id}'.")
            st.session_state["uploaded_to_astra"] = {}   # reset all flags
    st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    st.subheader("My files")
    if user_id:
        files = list_user_sources(user_id)
        if not files:
            st.write("No files yet for this user.")
        else:
            for name, full_source in files:
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.write(name)
                with c2:
                    delete_clicked = st.button("X", key=f"del_{full_source}")

                if delete_clicked:
                    if uploader_not_empty(uploaded):
                        st.warning("Please empty the uploader first (click X).")
                    else:
                        deleted = delete_user_file(user_id, full_source)
                        st.success(f"Deleted {deleted} chunks for {name}.")
                        st.session_state["uploaded_to_astra"].pop(name, None)
                        st.rerun()
    else:
        st.info("Enter a user id to see files.")


st.markdown(
    '<p class="big-question-label">Ask about your documents</p>',
    unsafe_allow_html=True
)
question = st.text_input("", key="question_input")
if st.button("Ask"):
    if question:
        start = time.perf_counter()
        answer, docs = rag_answer(question, user_id=user_id)
        ask_secs = time.perf_counter() - start
        st.caption(f"Answer took {ask_secs:.2f}s")

        st.write(answer)

        if docs:
            st.markdown("**Sources:**")
            for i, d in enumerate(docs):
                source = d.metadata.get("source", "unknown")
                page = d.metadata.get("page", "N/A")
                chunk_idx = d.metadata.get("chunk_index", "N/A")
                title = f"[{i+1}] {source} (page {page}, chunk {chunk_idx})"
                with st.expander(title):
                    st.write(d.page_content)
    else:
        st.write("Please type a question first.")












