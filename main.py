if __name__ == "__main__":
    from src.core.rag import DNDAssistant

    # Set your Obsidian vault path
    vault_path = "D:\Documents\DnD\ObsidianTTRPGVault-main"

    # Initialize the assistant
    assistant = DNDAssistant(
        vault_path=vault_path,
        homebrew_folders=["1-Party", "1-Session Journals", "2-Campaign", "2-World"]
    )

    # Parse and add notes to the vector store (uncomment to rebuild with new embeddings)
    # assistant.initialize_vault()

    # Run test queries with better search parameters
    questions = [
        "Does Averlyn have a king?",  # Non-existent location test
        "Who rules Srendia?",         # Known location test
        "What is the government of Marhaven?"  # Another known location
    ]
    
    for question in questions:
        print(f"\n{'='*100}")
        print(f"QUESTION: {question}")
        print('='*100)
        
        result = assistant.query(question, context_size=5, score_threshold=0.2)

        print("--- D&D Assistant Response ---")
        print(result["response"])
        print("\n" + "="*80)
        print("--- SOURCES FOUND ---")
        print("="*80)
        
        # Display sources
        sources = result["sources"]
        if sources:
            for i, source in enumerate(sources, 1):
                section_info = ""
                if source.metadata.get('is_section'):
                    section_info = f" → {source.metadata.get('section_title', 'Unknown Section')}"
                
                print(f"\n--- Source {i} ---")
                print(f"File: {source.metadata.get('file_title', 'Unknown')}{section_info}")
                print(f"Content Type: {source.metadata.get('content_type', 'Unknown')}")
                print(f"Folder: {source.metadata.get('folder', 'Unknown')}")
                print(f"Preview: {source.page_content[:200]}...")
        else:
            print("No sources found with current threshold!")
    
        print(f"Context size used: {result['context_used']}")
        print("\n" + "="*100)