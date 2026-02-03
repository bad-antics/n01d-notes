#!/usr/bin/env python3
"""
███╗   ██╗ ██████╗  ██╗██████╗       ███╗   ██╗ ██████╗ ████████╗███████╗███████╗
████╗  ██║██╔═████╗███║██╔══██╗      ████╗  ██║██╔═══██╗╚══██╔══╝██╔════╝██╔════╝
██╔██╗ ██║██║██╔██║╚██║██║  ██║█████╗██╔██╗ ██║██║   ██║   ██║   █████╗  ███████╗
██║╚██╗██║████╔╝██║ ██║██║  ██║╚════╝██║╚██╗██║██║   ██║   ██║   ██╔══╝  ╚════██║
██║ ╚████║╚██████╔╝ ██║██████╔╝      ██║ ╚████║╚██████╔╝   ██║   ███████╗███████║
╚═╝  ╚═══╝ ╚═════╝  ╚═╝╚═════╝       ╚═╝  ╚═══╝ ╚═════╝    ╚═╝   ╚══════╝╚══════╝

N01D Notes - Markdown note-taking with live preview
Part of the NullSec Toolkit
"""

import customtkinter as ctk
from pathlib import Path
from datetime import datetime
import json
import re
import os
from typing import Optional, Dict, List, Callable
import hashlib


VERSION = "1.0.0"
APP_NAME = "N01D Notes"


class N01DTheme:
    """N01D hacker theme"""
    
    def __init__(self):
        self.colors = {
            'bg_dark': '#0a0a0f',
            'bg': '#12121a',
            'bg_light': '#1a1a2e',
            'bg_lighter': '#252538',
            'accent': '#00ff88',
            'accent_dim': '#00cc66',
            'accent_hover': '#00dd77',
            'warning': '#ffaa00',
            'danger': '#ff3366',
            'info': '#00aaff',
            'text': '#e0e0e0',
            'text_dim': '#888888',
            'border': '#333344',
            'code_bg': '#1e1e2e',
            'heading': '#00ff88',
            'link': '#00aaff',
            'bold': '#ffffff',
        }
        
    def apply(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")


class NoteItem(ctk.CTkFrame):
    """Single note item in the sidebar"""
    
    def __init__(self, master, note_data: dict, theme: N01DTheme,
                 on_click: Callable, on_delete: Callable, **kwargs):
        super().__init__(master, **kwargs)
        
        self.note_id = note_data['id']
        self.theme = theme
        self.on_click = on_click
        self.on_delete = on_delete
        self.selected = False
        
        self.configure(
            fg_color="transparent",
            corner_radius=8,
            cursor="hand2"
        )
        
        # Make clickable
        self.bind("<Button-1>", lambda e: on_click(self.note_id))
        
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text=note_data.get('title', 'Untitled')[:30],
            font=ctk.CTkFont(family="JetBrains Mono", size=12, weight="bold"),
            anchor="w"
        )
        self.title_label.pack(fill="x", padx=10, pady=(8, 2))
        self.title_label.bind("<Button-1>", lambda e: on_click(self.note_id))
        
        # Preview text
        preview = note_data.get('content', '')[:50].replace('\n', ' ')
        self.preview_label = ctk.CTkLabel(
            self,
            text=preview or "Empty note",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=theme.colors['text_dim'],
            anchor="w"
        )
        self.preview_label.pack(fill="x", padx=10, pady=(0, 2))
        self.preview_label.bind("<Button-1>", lambda e: on_click(self.note_id))
        
        # Date
        date_str = note_data.get('modified', '')[:10]
        self.date_label = ctk.CTkLabel(
            self,
            text=date_str,
            font=ctk.CTkFont(family="JetBrains Mono", size=9),
            text_color=theme.colors['text_dim'],
            anchor="w"
        )
        self.date_label.pack(fill="x", padx=10, pady=(0, 8))
        self.date_label.bind("<Button-1>", lambda e: on_click(self.note_id))
        
    def set_selected(self, selected: bool):
        """Update selection state"""
        self.selected = selected
        if selected:
            self.configure(fg_color=self.theme.colors['bg_lighter'])
        else:
            self.configure(fg_color="transparent")
            
    def update_data(self, note_data: dict):
        """Update displayed data"""
        self.title_label.configure(text=note_data.get('title', 'Untitled')[:30])
        preview = note_data.get('content', '')[:50].replace('\n', ' ')
        self.preview_label.configure(text=preview or "Empty note")
        self.date_label.configure(text=note_data.get('modified', '')[:10])


class MarkdownPreview(ctk.CTkFrame):
    """Markdown preview panel with basic rendering"""
    
    def __init__(self, master, theme: N01DTheme, **kwargs):
        super().__init__(master, **kwargs)
        
        self.theme = theme
        self.configure(fg_color=theme.colors['bg_light'], corner_radius=10)
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header,
            text="📖 Preview",
            font=ctk.CTkFont(family="JetBrains Mono", size=12, weight="bold"),
            text_color=theme.colors['text_dim']
        ).pack(side="left")
        
        # Scrollable preview
        self.preview_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.preview_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
    def render(self, markdown_text: str):
        """Render markdown to preview"""
        # Clear current
        for widget in self.preview_scroll.winfo_children():
            widget.destroy()
            
        if not markdown_text.strip():
            ctk.CTkLabel(
                self.preview_scroll,
                text="Start typing to see preview...",
                font=ctk.CTkFont(family="JetBrains Mono", size=12),
                text_color=self.theme.colors['text_dim']
            ).pack(anchor="w", pady=10)
            return
            
        lines = markdown_text.split('\n')
        in_code_block = False
        code_lines = []
        
        for line in lines:
            # Code blocks
            if line.startswith('```'):
                if in_code_block:
                    # End code block
                    self._add_code_block('\n'.join(code_lines))
                    code_lines = []
                in_code_block = not in_code_block
                continue
                
            if in_code_block:
                code_lines.append(line)
                continue
                
            # Headers
            if line.startswith('# '):
                self._add_heading(line[2:], 1)
            elif line.startswith('## '):
                self._add_heading(line[3:], 2)
            elif line.startswith('### '):
                self._add_heading(line[4:], 3)
            elif line.startswith('#### '):
                self._add_heading(line[5:], 4)
            # Bullet points
            elif line.startswith('- ') or line.startswith('* '):
                self._add_bullet(line[2:])
            # Numbered list
            elif re.match(r'^\d+\. ', line):
                text = re.sub(r'^\d+\. ', '', line)
                self._add_numbered(line[:line.index('.')], text)
            # Blockquote
            elif line.startswith('> '):
                self._add_blockquote(line[2:])
            # Horizontal rule
            elif line.strip() in ['---', '***', '___']:
                self._add_hr()
            # Regular text
            elif line.strip():
                self._add_paragraph(line)
            # Empty line
            else:
                self._add_spacer()
                
    def _add_heading(self, text: str, level: int):
        sizes = {1: 24, 2: 20, 3: 16, 4: 14}
        ctk.CTkLabel(
            self.preview_scroll,
            text=text,
            font=ctk.CTkFont(family="JetBrains Mono", size=sizes.get(level, 14), weight="bold"),
            text_color=self.theme.colors['heading'],
            anchor="w",
            wraplength=500
        ).pack(fill="x", anchor="w", pady=(10 if level == 1 else 5, 5))
        
    def _add_paragraph(self, text: str):
        # Handle inline formatting
        text = self._format_inline(text)
        ctk.CTkLabel(
            self.preview_scroll,
            text=text,
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            anchor="w",
            wraplength=500,
            justify="left"
        ).pack(fill="x", anchor="w", pady=2)
        
    def _format_inline(self, text: str) -> str:
        # Remove markdown formatting for display
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)  # Italic
        text = re.sub(r'`(.+?)`', r'\1', text)  # Inline code
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # Links
        return text
        
    def _add_bullet(self, text: str):
        frame = ctk.CTkFrame(self.preview_scroll, fg_color="transparent")
        frame.pack(fill="x", anchor="w", pady=2)
        
        ctk.CTkLabel(
            frame,
            text="•",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            text_color=self.theme.colors['accent'],
            width=20
        ).pack(side="left")
        
        ctk.CTkLabel(
            frame,
            text=self._format_inline(text),
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            anchor="w",
            wraplength=480
        ).pack(side="left", fill="x")
        
    def _add_numbered(self, num: str, text: str):
        frame = ctk.CTkFrame(self.preview_scroll, fg_color="transparent")
        frame.pack(fill="x", anchor="w", pady=2)
        
        ctk.CTkLabel(
            frame,
            text=f"{num}.",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            text_color=self.theme.colors['accent'],
            width=25
        ).pack(side="left")
        
        ctk.CTkLabel(
            frame,
            text=self._format_inline(text),
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            anchor="w",
            wraplength=475
        ).pack(side="left", fill="x")
        
    def _add_blockquote(self, text: str):
        frame = ctk.CTkFrame(
            self.preview_scroll,
            fg_color=self.theme.colors['bg_lighter'],
            corner_radius=5
        )
        frame.pack(fill="x", anchor="w", pady=5, padx=(10, 0))
        
        # Left border
        border = ctk.CTkFrame(frame, fg_color=self.theme.colors['accent'], width=3)
        border.pack(side="left", fill="y")
        
        ctk.CTkLabel(
            frame,
            text=text,
            font=ctk.CTkFont(family="JetBrains Mono", size=11, slant="italic"),
            text_color=self.theme.colors['text_dim'],
            anchor="w",
            wraplength=470
        ).pack(side="left", padx=10, pady=8)
        
    def _add_code_block(self, code: str):
        frame = ctk.CTkFrame(
            self.preview_scroll,
            fg_color=self.theme.colors['code_bg'],
            corner_radius=8
        )
        frame.pack(fill="x", anchor="w", pady=5)
        
        ctk.CTkLabel(
            frame,
            text=code,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            anchor="w",
            justify="left"
        ).pack(fill="x", padx=15, pady=10)
        
    def _add_hr(self):
        ctk.CTkFrame(
            self.preview_scroll,
            fg_color=self.theme.colors['border'],
            height=1
        ).pack(fill="x", pady=10)
        
    def _add_spacer(self):
        ctk.CTkFrame(
            self.preview_scroll,
            fg_color="transparent",
            height=10
        ).pack(fill="x")


class N01DNotes(ctk.CTk):
    """Main Notes Application"""
    
    def __init__(self):
        super().__init__()
        
        self.theme = N01DTheme()
        self.theme.apply()
        
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("1400x800")
        self.minsize(1000, 600)
        self.configure(fg_color=self.theme.colors['bg_dark'])
        
        # Data
        self.notes_dir = Path.home() / ".n01d-notes"
        self.notes_dir.mkdir(exist_ok=True)
        self.notes_file = self.notes_dir / "notes.json"
        
        self.notes: Dict[str, dict] = {}
        self.current_note_id: Optional[str] = None
        self.note_items: Dict[str, NoteItem] = {}
        
        self._load_notes()
        
        # Grid config
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_sidebar()
        self._create_editor()
        self._create_preview()
        
        # Key bindings
        self.bind("<Control-n>", lambda e: self._new_note())
        self.bind("<Control-s>", lambda e: self._save_current())
        self.bind("<Control-d>", lambda e: self._delete_current())
        
        # Select first note or create one
        if self.notes:
            first_id = list(self.notes.keys())[0]
            self._select_note(first_id)
        else:
            self._new_note()
            
    def _create_sidebar(self):
        """Create left sidebar with notes list"""
        sidebar = ctk.CTkFrame(
            self,
            fg_color=self.theme.colors['bg'],
            width=280,
            corner_radius=0
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        
        # Header
        header = ctk.CTkFrame(sidebar, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=15)
        
        title = ctk.CTkLabel(
            header,
            text="N01D",
            font=ctk.CTkFont(family="JetBrains Mono", size=24, weight="bold"),
            text_color=self.theme.colors['accent']
        )
        title.pack(side="left")
        
        subtitle = ctk.CTkLabel(
            header,
            text="NOTES",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=self.theme.colors['text_dim']
        )
        subtitle.pack(side="left", padx=5, pady=8)
        
        # New note button
        new_btn = ctk.CTkButton(
            sidebar,
            text="+ New Note",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            fg_color=self.theme.colors['accent'],
            text_color="black",
            hover_color=self.theme.colors['accent_hover'],
            height=40,
            command=self._new_note
        )
        new_btn.pack(fill="x", padx=15, pady=(0, 15))
        
        # Search
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_notes())
        
        search = ctk.CTkEntry(
            sidebar,
            placeholder_text="🔍 Search notes...",
            textvariable=self.search_var,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            height=35
        )
        search.pack(fill="x", padx=15, pady=(0, 10))
        
        # Separator
        ctk.CTkFrame(
            sidebar,
            fg_color=self.theme.colors['border'],
            height=1
        ).pack(fill="x", padx=15, pady=5)
        
        # Notes list
        self.notes_scroll = ctk.CTkScrollableFrame(
            sidebar,
            fg_color="transparent"
        )
        self.notes_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self._refresh_notes_list()
        
        # Bottom stats
        self.stats_label = ctk.CTkLabel(
            sidebar,
            text=f"{len(self.notes)} notes",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=self.theme.colors['text_dim']
        )
        self.stats_label.pack(pady=10)
        
    def _create_editor(self):
        """Create main editor area"""
        editor_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme.colors['bg_light'],
            corner_radius=10
        )
        editor_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 5), pady=10)
        editor_frame.grid_rowconfigure(1, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)
        
        # Title input
        title_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        
        self.title_entry = ctk.CTkEntry(
            title_frame,
            placeholder_text="Note title...",
            font=ctk.CTkFont(family="JetBrains Mono", size=18, weight="bold"),
            fg_color="transparent",
            border_width=0,
            height=40
        )
        self.title_entry.pack(fill="x", side="left", expand=True)
        self.title_entry.bind("<KeyRelease>", self._on_title_change)
        
        # Delete button
        delete_btn = ctk.CTkButton(
            title_frame,
            text="🗑️",
            width=40,
            height=40,
            fg_color="transparent",
            hover_color=self.theme.colors['danger'] + "40",
            command=self._delete_current
        )
        delete_btn.pack(side="right")
        
        # Editor
        self.editor = ctk.CTkTextbox(
            editor_frame,
            font=ctk.CTkFont(family="JetBrains Mono", size=13),
            fg_color=self.theme.colors['bg'],
            wrap="word",
            corner_radius=8
        )
        self.editor.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.editor.bind("<KeyRelease>", self._on_content_change)
        
        # Toolbar
        toolbar = ctk.CTkFrame(editor_frame, fg_color="transparent")
        toolbar.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        buttons = [
            ("**B**", self._insert_bold),
            ("*I*", self._insert_italic),
            ("`C`", self._insert_code),
            ("H1", lambda: self._insert_heading(1)),
            ("H2", lambda: self._insert_heading(2)),
            ("- •", self._insert_bullet),
            ("🔗", self._insert_link),
            ("📷", self._insert_image),
        ]
        
        for text, cmd in buttons:
            btn = ctk.CTkButton(
                toolbar,
                text=text,
                width=40,
                height=30,
                fg_color=self.theme.colors['bg_lighter'],
                hover_color=self.theme.colors['accent'] + "40",
                font=ctk.CTkFont(family="JetBrains Mono", size=10),
                command=cmd
            )
            btn.pack(side="left", padx=2)
            
        # Word count
        self.word_count = ctk.CTkLabel(
            toolbar,
            text="0 words",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=self.theme.colors['text_dim']
        )
        self.word_count.pack(side="right")
        
    def _create_preview(self):
        """Create preview panel"""
        self.preview = MarkdownPreview(self, self.theme)
        self.preview.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
        
    def _load_notes(self):
        """Load notes from JSON file"""
        if self.notes_file.exists():
            try:
                with open(self.notes_file, 'r') as f:
                    self.notes = json.load(f)
            except:
                self.notes = {}
        else:
            self.notes = {}
            
    def _save_notes(self):
        """Save all notes to JSON file"""
        with open(self.notes_file, 'w') as f:
            json.dump(self.notes, f, indent=2)
            
    def _refresh_notes_list(self):
        """Refresh the notes list in sidebar"""
        # Clear current
        for widget in self.notes_scroll.winfo_children():
            widget.destroy()
        self.note_items.clear()
        
        # Sort by modified date
        sorted_notes = sorted(
            self.notes.items(),
            key=lambda x: x[1].get('modified', ''),
            reverse=True
        )
        
        search = self.search_var.get().lower() if hasattr(self, 'search_var') else ''
        
        for note_id, note_data in sorted_notes:
            # Filter by search
            if search:
                if search not in note_data.get('title', '').lower() and \
                   search not in note_data.get('content', '').lower():
                    continue
                    
            item = NoteItem(
                self.notes_scroll,
                note_data,
                self.theme,
                on_click=self._select_note,
                on_delete=self._delete_note
            )
            item.pack(fill="x", pady=2)
            self.note_items[note_id] = item
            
            if note_id == self.current_note_id:
                item.set_selected(True)
                
        # Update stats
        if hasattr(self, 'stats_label'):
            self.stats_label.configure(text=f"{len(self.notes)} notes")
            
    def _filter_notes(self):
        """Filter notes by search term"""
        self._refresh_notes_list()
        
    def _new_note(self):
        """Create a new note"""
        note_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]
        now = datetime.now().isoformat()
        
        self.notes[note_id] = {
            'id': note_id,
            'title': 'New Note',
            'content': '',
            'created': now,
            'modified': now
        }
        
        self._save_notes()
        self._refresh_notes_list()
        self._select_note(note_id)
        
        # Focus title
        self.title_entry.focus_set()
        self.title_entry.select_range(0, 'end')
        
    def _select_note(self, note_id: str):
        """Select and load a note"""
        # Save current first
        if self.current_note_id and self.current_note_id in self.notes:
            self._save_current()
            
        # Update selection UI
        if self.current_note_id in self.note_items:
            self.note_items[self.current_note_id].set_selected(False)
            
        self.current_note_id = note_id
        
        if note_id in self.note_items:
            self.note_items[note_id].set_selected(True)
            
        # Load note content
        note = self.notes.get(note_id, {})
        
        self.title_entry.delete(0, 'end')
        self.title_entry.insert(0, note.get('title', 'Untitled'))
        
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", note.get('content', ''))
        
        # Update preview
        self.preview.render(note.get('content', ''))
        self._update_word_count()
        
    def _save_current(self):
        """Save current note"""
        if not self.current_note_id:
            return
            
        if self.current_note_id not in self.notes:
            return
            
        title = self.title_entry.get().strip() or "Untitled"
        content = self.editor.get("1.0", "end-1c")
        
        self.notes[self.current_note_id]['title'] = title
        self.notes[self.current_note_id]['content'] = content
        self.notes[self.current_note_id]['modified'] = datetime.now().isoformat()
        
        self._save_notes()
        
        # Update sidebar item
        if self.current_note_id in self.note_items:
            self.note_items[self.current_note_id].update_data(
                self.notes[self.current_note_id]
            )
            
    def _delete_note(self, note_id: str):
        """Delete a note"""
        if note_id in self.notes:
            del self.notes[note_id]
            self._save_notes()
            
        if note_id == self.current_note_id:
            self.current_note_id = None
            self.title_entry.delete(0, 'end')
            self.editor.delete("1.0", "end")
            
        self._refresh_notes_list()
        
        # Select first note if exists
        if self.notes:
            first_id = list(self.notes.keys())[0]
            self._select_note(first_id)
            
    def _delete_current(self):
        """Delete current note"""
        if self.current_note_id:
            self._delete_note(self.current_note_id)
            
    def _on_title_change(self, event=None):
        """Handle title change"""
        self._save_current()
        
    def _on_content_change(self, event=None):
        """Handle content change"""
        content = self.editor.get("1.0", "end-1c")
        self.preview.render(content)
        self._update_word_count()
        
        # Auto-save
        self._save_current()
        
    def _update_word_count(self):
        """Update word count display"""
        content = self.editor.get("1.0", "end-1c")
        words = len(content.split())
        chars = len(content)
        self.word_count.configure(text=f"{words} words • {chars} chars")
        
    # Formatting helpers
    def _insert_bold(self):
        self._wrap_selection("**", "**")
        
    def _insert_italic(self):
        self._wrap_selection("*", "*")
        
    def _insert_code(self):
        self._wrap_selection("`", "`")
        
    def _insert_heading(self, level: int):
        prefix = "#" * level + " "
        self.editor.insert("insert linestart", prefix)
        
    def _insert_bullet(self):
        self.editor.insert("insert linestart", "- ")
        
    def _insert_link(self):
        self._wrap_selection("[", "](url)")
        
    def _insert_image(self):
        self.editor.insert("insert", "![alt text](image_url)")
        
    def _wrap_selection(self, prefix: str, suffix: str):
        """Wrap selected text with prefix and suffix"""
        try:
            sel_start = self.editor.index("sel.first")
            sel_end = self.editor.index("sel.last")
            selected = self.editor.get(sel_start, sel_end)
            self.editor.delete(sel_start, sel_end)
            self.editor.insert(sel_start, f"{prefix}{selected}{suffix}")
        except:
            self.editor.insert("insert", f"{prefix}text{suffix}")


def main():
    app = N01DNotes()
    app.mainloop()
    

if __name__ == "__main__":
    main()
