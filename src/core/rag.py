# RAG pipeline
from langchain.chains import create_retrieval_chain
from .embeddings import VectorStore
from .llm import DNDLLMInterface
from ..obsidian.parser import ObsidianParser

class DNDAssistant:
    def __init__(
            self,
            vault_path: str,
            homebrew_folders: list = [],
            model_name = 'mistral:7b'
    ):
        self.parser = ObsidianParser(
            vault_path,
            homebrew_folders=homebrew_folders
        )
        self.vector_store = VectorStore()

        # Use the LLM interface
        self.llm_interface = DNDLLMInterface(model_name=model_name)
        self.combine_docs_chain = self.llm_interface.get_combine_docs_chain()

    def initialize_vault(self):
        notes = self.parser.parse_vault()
        self.vector_store.add_notes(notes)
    
    def query(
            self,
            question,
            folder_filter=None,
            context_size=5,
            score_threshold=0.3  # Much lower threshold for better recall
    ):
        # Use standard retriever
        retriever = self.vector_store.get_retriever(
            k=context_size, 
            score_threshold=score_threshold
        )
        
        # Build chain for this query
        qa_chain = create_retrieval_chain(
            retriever=retriever,
            combine_docs_chain=self.combine_docs_chain
        )
        result = qa_chain.invoke({"input": question, "question": question})
        response = result.get("answer", "")
        sources = result.get("context", [])
        return {
            "response": response,
            "sources": sources,
            "context_used": len(sources)
        }
