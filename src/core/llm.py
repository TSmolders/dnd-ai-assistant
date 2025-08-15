# LLM interface
from langchain_ollama import ChatOllama
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)

class DNDLLMInterface:
    def __init__(self, model_name='mistral:7b', temperature=0.2, max_tokens=2000):
        self.chat_model = ChatOllama(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens
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

    def get_combine_docs_chain(self):
        return self.combine_docs_chain
