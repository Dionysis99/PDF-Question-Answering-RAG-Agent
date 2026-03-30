from pypdf import PdfReader
from langchain_core.documents import Document
import os


def load_pdf_as_docs(path: str) -> list[Document]:
    reader = PdfReader(path)
    filename = os.path.basename(path)  # temp filename, will be overridden later if needed
    docs: list[Document] = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": filename,
                    "page": page_num,
                },
            )
        )
    return docs


def load_paths_as_docs(paths: list[str]) -> list[Document]:
    all_docs: list[Document] = []
    for p in paths:
        all_docs.extend(load_pdf_as_docs(p))
    return all_docs