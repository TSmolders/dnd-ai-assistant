# Vector database management
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import List, Dict
from ..obsidian.parser import ObsidianParser

class VectorStore:
    def __init__(self, persist_dir = './data/vector_store'):
        self.embedder = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        self.chroma = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embedder,
            collection_name="dnd_vault"
        )
    
    def add_notes(self, notes):
        docs = []
        for i, note in enumerate(notes):
            text = f'From {note.folder}:\n# {note.title}\n\n{note.content}'
            doc = Document(
                page_content=text,
                metadata={
                    "title": note.title,
                    "path": note.path,
                    "folder": note.folder,
                    "tags": ', '.join(note.tags)
                },
                id=f"note_{i}"
            )
            docs.append(doc)
        self.chroma.add_documents(docs)

    def get_retriever(self, k=5, score_threshold=0.8):
        return self.chroma.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": score_threshold, "k": k}
        )
