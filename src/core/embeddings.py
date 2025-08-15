# Vector database management
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import List, Dict
from ..obsidian.parser import ObsidianParser

class VectorStore:
    def __init__(self, persist_dir = './data/vector_store'):
        # Use a better embedding model for improved semantic understanding
        self.embedder = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",  # Better than MiniLM
            model_kwargs={'device': 'cpu'},  # Explicitly set device
            encode_kwargs={'normalize_embeddings': True}  # Normalize for better similarity
        )
        self.chroma = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embedder,
            collection_name="dnd_vault"
        )
    
    def add_notes(self, notes, batch_size=1000):
        """Add notes to the vector store in batches to avoid size limits."""
        docs = []
        for i, note in enumerate(notes):
            # Create enhanced text that includes more searchable metadata
            metadata_text = ""
            if note.tags:
                metadata_text += f"Tags: {', '.join(note.tags)}. "
            
            # Include parent folder context for better geographical/categorical matching
            folder_context = note.folder.replace("[HOMEBREW]", "").replace("[GENERAL]", "").strip()
            
            # Create a more descriptive text for sections
            if note.is_section:
                # Include file title and section for better context
                text = f'Location: {folder_context}\n{metadata_text}File: {note.metadata.get("file_title", "Unknown File")}, Section: {note.section_title}\n\n{note.content}'
            else:
                text = f'Location: {folder_context}\n{metadata_text}Title: {note.title}\n\n{note.content}'
            
            doc = Document(
                page_content=text,
                metadata={
                    "title": note.title,
                    "file_title": note.metadata.get('file_title', note.title),
                    "section_title": note.section_title,
                    "section_level": note.section_level,
                    "is_section": note.is_section,
                    "path": note.path,
                    "folder": note.folder,
                    "content_type": note.metadata.get('content_type', 'unknown'),
                    "tags": ', '.join(note.tags)
                },
                id=f"section_{i}"
            )
            docs.append(doc)
        
        # Add documents in batches
        total_docs = len(docs)
        print(f"Adding {total_docs} documents in batches of {batch_size}...")
        
        for i in range(0, total_docs, batch_size):
            batch = docs[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_docs + batch_size - 1) // batch_size
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)")
            self.chroma.add_documents(batch)
        
        print(f"Successfully added all {total_docs} documents to the vector store.")

    def get_retriever(self, k=5, score_threshold=0.5):  # Lowered default threshold
        return self.chroma.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": score_threshold, "k": k}
        )