# Obsidian vault processing
import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ObsidianNote:
    path: str
    title: str
    content: str
    metadata: Dict
    tags: List[str]
    links: List[str]
    folder: str

class ObsidianParser:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
    
    def parse_frontmatter(self, text):
        metadata = {}
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                frontmatter = text[3:end].strip()
                try:
                    metadata = yaml.safe_load(frontmatter) or {}
                except yaml.YAMLError:
                    metadata = {}
                text = text[end + 3:].strip()
        return metadata, text

    def extract_tags(self, text, metadata):
        tags = []
        # Frontmatter tags
        fm_tags = metadata.get('tags', [])
        if isinstance(fm_tags, str):
            tags.append(fm_tags)
        elif isinstance(fm_tags, list):
            tags.extend(fm_tags)
        # Inline tags
        inline_tags = re.findall(r'#([A-Za-z0-9/_-]+)', text)
        tags.extend(inline_tags)
        return list(set(tags))  # Remove duplicates

    def extract_links(self, text):
        wikilinks = re.findall(r'\[\[([^\]]+)\]\]', text)
        mdlinks = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
        md_targets = [t[1] for t in mdlinks]
        return wikilinks + md_targets
    
    def parse_note(self, file_path: Path):
        try:
            raw = file_path.read_text('utf-8')
        except Exception:
            return None
        metadata, body = self.parse_frontmatter(raw)
        title = metadata.get('title', file_path.stem)
        tags = self.extract_tags(body, metadata)
        links = self.extract_links(body)
        folder = str(file_path.parent.name)
        return ObsidianNote(
            path=str(file_path),
            title=title,
            content=body,
            metadata=metadata,
            tags=tags,
            links=links,
            folder=folder
        )

    def parse_vault(self):
        notes = []
        for md in self.vault_path.rglob('*.md'):
            note = self.parse_note(md)
            if note:
                notes.append(note)
        print(f'Parsed {len(notes)} notes from the vault.')
        return notes

# test
# if __name__ == "__main__":
#     parser = ObsidianParser("D:\\Documents\\DnD\\ObsidianTTRPGVault-main - BackUp")
#     notes = parser.parse_vault()
#     print(f"Found {len(notes)} notes.")
#     print(f"Title of the first note: {notes[145].title}")
#     print(f"Content of the first note: {notes[145].content}")
#     print(f"Metadata of the first note: {notes[145].metadata}")
#     print(f"Tags of the first note: {notes[145].tags}")
#     print(f"Links of the first note: {notes[145].links}")
#     print(f"Folder of the first note: {notes[145].folder}")