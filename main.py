if __name__ == "__main__":
    from src.core.rag import DNDAssistant

    # Set your Obsidian vault path
    vault_path = "D:\Documents\DnD\ObsidianTTRPGVault-main"

    # Initialize the assistant
    assistant = DNDAssistant(vault_path=vault_path)

    # Parse and add notes to the vector store
    # assistant.initialize_vault()

    # Run a test query
    question = "Does Averlyn have a king?"
    result = assistant.query(question, context_size=10, score_threshold=0.1)

    print("--- D&D Assistant Response ---")
    print(result["response"])
    print("--- Sources Used ---")
    for source in result["sources"]:
        print(f"Title: {source.metadata.get('title', 'Unknown')}, Folder: {source.metadata.get('folder', 'Unknown')}")
    print(f"Context size: {result['context_used']}")