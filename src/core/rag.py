# RAG pipeline
from langchain_ollama import ChatOllama
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from .embeddings import VectorStore

class DNDAssistant:
    def __init__(
            self,
            vault_path: str,
            model_name = 'mistral:7b'
    ):
        from ..obsidian.parser import ObsidianParser
        self.parser = ObsidianParser(vault_path)
        self.vector_store = VectorStore()

        # Store model and prompt setup for later use
        self.chat_model = ChatOllama(
            model=model_name,
            temperature=0.2,
            max_tokens=2000
        )
        self.custom_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "You are an expert Dungeons and Dragons assistant. Use provided context to answer consistently, prioritizing campaign lore. Answer ONLY using the provided context. If the answer is not present in the context, reply strictly with \"I don't know\" and do NOT make up information. Example:\nContext: [empty]\nQuestion: Who is the king?\nAnswer: I don't know"
            ),
            HumanMessagePromptTemplate.from_template(
                "Context:\n{context}\n\nQuestion: {question}\n\nProvide a detailed response only based on the context. Answer ONLY using the provided context. If the answer is not present in the context, let the user know truthfully."
            )
        ])
        self.combine_docs_chain = create_stuff_documents_chain(
            self.chat_model,
            self.custom_prompt
        )

    def initialize_vault(self):
        notes = self.parser.parse_vault()
        self.vector_store.add_notes(notes)
    
    def query(
            self,
            question,
            folder_filter=None,
            context_size=5,
            score_threshold=0.8
    ):
        # Build retriever with current search parameters
        search_kwargs = {"k": context_size, "score_threshold": score_threshold}
        if folder_filter:
            search_kwargs["filter"] = {"folder": folder_filter}
        retriever = self.vector_store.get_retriever(**search_kwargs)
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
