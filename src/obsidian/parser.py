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
    section_title: str = ""
    section_level: int = 0
    is_section: bool = False

class ObsidianParser:
    def __init__(self, vault_path, homebrew_folders: List[str] = []):
        self.vault_path = Path(vault_path)
        self.homebrew_folders = homebrew_folders

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

    def remove_leaflet_blocks(self, text):
        """Remove leaflet code blocks from the text."""
        # Remove leaflet blocks using regex
        pattern = r'```leaflet\s*\n.*?\n```'
        cleaned_text = re.sub(pattern, '', text, flags=re.DOTALL)
        # Clean up any extra whitespace left behind
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text).strip()
        return cleaned_text

    def split_into_sections(self, content: str):
        """Split content into sections based on markdown headers."""
        sections = []
        
        # Split by headers (# ## ### etc.)
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = content.split('\n')
        
        current_section_content = []
        current_header = ""
        current_level = 0
        preamble_content = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            header_match = re.match(header_pattern, line)
            
            if header_match:
                # Save previous section or preamble
                if current_header:
                    section_content = '\n'.join(current_section_content).strip()
                    if section_content:
                        sections.append({
                            'title': current_header,
                            'level': current_level,
                            'content': section_content
                        })
                elif current_section_content or preamble_content:
                    # This is content before the first header
                    preamble = '\n'.join(preamble_content + current_section_content).strip()
                    if preamble:
                        sections.append({
                            'title': '',
                            'level': 0,
                            'content': preamble
                        })
                
                # Start new section
                current_level = len(header_match.group(1))
                current_header = header_match.group(2).strip()
                current_section_content = []
            else:
                # Add line to current section or preamble
                if current_header:
                    current_section_content.append(line)
                else:
                    preamble_content.append(line)
            
            i += 1
        
        # Handle the last section
        if current_header and current_section_content:
            section_content = '\n'.join(current_section_content).strip()
            if section_content:
                sections.append({
                    'title': current_header,
                    'level': current_level,
                    'content': section_content
                })
        elif not sections and (current_section_content or preamble_content):
            # File has no headers, treat as single section
            all_content = '\n'.join(preamble_content + current_section_content).strip()
            if all_content:
                sections.append({
                    'title': '',
                    'level': 0,
                    'content': all_content
                })
        
        return sections

    def get_content_type(self, folder_path: str, homebrew_folders: List[str]):
        """Determine if content is homebrew or general D&D based on folder naming."""
        if not folder_path:
            return "general"
        
        # Get the top-level folder name
        top_folder = folder_path.split('/')[0] if '/' in folder_path else folder_path.split('\\')[0]
        
        # Check if the top folder is in homebrew_folders
        if top_folder in homebrew_folders:
            return "homebrew"
        else:
            return "general"

    def parse_note(self, file_path: Path):
        try:
            raw = file_path.read_text('utf-8')
        except Exception:
            return []
        
        metadata, body = self.parse_frontmatter(raw)
        
        # Remove leaflet blocks from the body content
        body = self.remove_leaflet_blocks(body)
        
        file_title = metadata.get('title', file_path.stem)
        base_tags = self.extract_tags(body, metadata)
        base_links = self.extract_links(body)
        
        # Get the full folder path relative to the vault root
        relative_path = file_path.relative_to(self.vault_path)
        folder = str(relative_path.parent) if relative_path.parent != Path('.') else ''
        
        # Determine content type and enhance folder information
        content_type = self.get_content_type(folder, self.homebrew_folders)
        enhanced_folder = f"[{content_type.upper()}] {folder}" if folder else f"[{content_type.upper()}]"
        
        # Add content type to metadata
        metadata['content_type'] = content_type
        
        # Split into sections
        sections = self.split_into_sections(body)
        notes = []
        
        for section in sections:
            # Extract tags and links specific to this section
            section_tags = self.extract_tags(section['content'], {})
            section_links = self.extract_links(section['content'])
            
            # Combine file-level and section-level tags/links
            all_tags = list(set(base_tags + section_tags))
            all_links = list(set(base_links + section_links))
            
            # Create section metadata
            section_metadata = metadata.copy()
            section_metadata['section_title'] = section['title']
            section_metadata['section_level'] = section['level']
            section_metadata['file_title'] = file_title
            
            note = ObsidianNote(
                path=str(file_path),
                title=f"{file_title} - {section['title']}" if section['title'] else file_title,
                content=section['content'],
                metadata=section_metadata,
                tags=all_tags,
                links=all_links,
                folder=enhanced_folder,
                section_title=section['title'],
                section_level=section['level'],
                is_section=bool(section['title'])
            )
            notes.append(note)
        
        return notes

    def parse_vault(self):
        notes = []
        total_files = 0
        total_sections = 0
        
        for md in self.vault_path.rglob('*.md'):
            total_files += 1
            file_notes = self.parse_note(md)
            if file_notes:
                notes.extend(file_notes)
                total_sections += len(file_notes)
        
        print(f'Parsed {total_files} files into {total_sections} sections from the vault.')
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