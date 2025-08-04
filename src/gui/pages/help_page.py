"""
Help page implementation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import webbrowser

from src.gui.page_manager import BasePage
from src.storage.help_content_storage import get_help_content_storage
from src.models.help_models import HelpContent, FAQItem, ContactInfo, SearchResult


class HelpPage(BasePage):
    """Help and support page with full content management."""
    
    def __init__(self, parent: tk.Widget):
        """Initialize help page."""
        super().__init__(parent, "Help", "說明文件")
        self.help_storage = get_help_content_storage()
        self.search_var = tk.StringVar()
        self.current_content: Optional[HelpContent] = None
        self.faq_frames: List[tk.Widget] = []
    
    def initialize_content(self) -> None:
        """Initialize page content (called once)."""
        if not self.frame:
            return
        
        # Page title
        title_label = ttk.Label(
            self.frame,
            text="Help & Support",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        subtitle_label = ttk.Label(
            self.frame,
            text="使用指南、FAQ和支援資訊",
            font=("Segoe UI", 10),
            foreground="#666666"
        )
        subtitle_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Create search panel
        self._create_search_panel()
        
        # Create notebook for different sections
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create tabs
        self._create_about_tab()
        self._create_faq_tab()
        self._create_contact_tab()
        
        # Load content
        self._load_help_content()
    
    def _create_search_panel(self) -> None:
        """Create search panel."""
        search_frame = ttk.LabelFrame(self.frame, text="搜尋說明內容", padding=10)
        search_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        search_row = ttk.Frame(search_frame)
        search_row.pack(fill=tk.X)
        
        ttk.Label(search_row, text="搜尋:").pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        search_entry.bind('<Return>', lambda e: self._perform_search())
        
        search_btn = ttk.Button(search_row, text="搜尋", command=self._perform_search)
        search_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = ttk.Button(search_row, text="清除", command=self._clear_search)
        clear_btn.pack(side=tk.LEFT)
    
    def _create_about_tab(self) -> None:
        """Create about/introduction tab."""
        about_frame = ttk.Frame(self.notebook)
        self.notebook.add(about_frame, text="關於應用程式")
        
        # Create scrollable text widget
        text_frame = ttk.Frame(about_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.about_text = tk.Text(
            text_frame, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            font=("Segoe UI", 10),
            bg="#f8f9fa",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        
        about_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.about_text.yview)
        self.about_text.configure(yscrollcommand=about_scrollbar.set)
        
        self.about_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        about_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_faq_tab(self) -> None:
        """Create FAQ tab."""
        faq_frame = ttk.Frame(self.notebook)
        self.notebook.add(faq_frame, text="常見問題")
        
        # Create scrollable frame for FAQ items
        canvas = tk.Canvas(faq_frame, bg="#ffffff")
        scrollbar = ttk.Scrollbar(faq_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.faq_scrollable_frame = ttk.Frame(canvas)
        
        self.faq_scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.faq_scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
    
    def _create_contact_tab(self) -> None:
        """Create contact information tab."""
        contact_frame = ttk.Frame(self.notebook)
        self.notebook.add(contact_frame, text="聯絡支援")
        
        # Create contact info display
        contact_container = ttk.Frame(contact_frame)
        contact_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(
            contact_container,
            text="聯絡我們",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Contact details frame
        self.contact_details_frame = ttk.LabelFrame(contact_container, text="支援資訊", padding=20)
        self.contact_details_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(contact_container, text="說明內容統計", padding=20)
        stats_frame.pack(fill=tk.X)
        
        self.stats_text = tk.Text(
            stats_frame,
            height=8,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Segoe UI", 10),
            bg="#f8f9fa",
            relief=tk.FLAT
        )
        self.stats_text.pack(fill=tk.X)
    
    def _load_help_content(self) -> None:
        """Load help content from storage."""
        try:
            self.current_content = self.help_storage.load_help_content()
            self._update_about_content()
            self._update_faq_content()
            self._update_contact_content()
            self._update_statistics()
        except Exception as e:
            messagebox.showerror("錯誤", f"載入說明內容時發生錯誤: {e}")
    
    def _update_about_content(self) -> None:
        """Update about tab content."""
        if not self.current_content:
            return
        
        self.about_text.config(state=tk.NORMAL)
        self.about_text.delete(1.0, tk.END)
        self.about_text.insert(tk.END, self.current_content.about_text)
        self.about_text.config(state=tk.DISABLED)
    
    def _update_faq_content(self) -> None:
        """Update FAQ tab content."""
        if not self.current_content:
            return
        
        # Clear existing FAQ frames
        for frame in self.faq_frames:
            frame.destroy()
        self.faq_frames.clear()
        
        # Group FAQ items by category
        categories = {}
        for faq in self.current_content.faq_items:
            if faq.category not in categories:
                categories[faq.category] = []
            categories[faq.category].append(faq)
        
        # Sort categories and items
        for category in categories:
            categories[category].sort(key=lambda x: x.order)
        
        # Create FAQ sections
        for category in sorted(categories.keys()):
            self._create_faq_category(category, categories[category])
    
    def _create_faq_category(self, category: str, faq_items: List[FAQItem]) -> None:
        """Create FAQ category section."""
        # Category header
        category_frame = ttk.LabelFrame(self.faq_scrollable_frame, text=category, padding=10)
        category_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.faq_frames.append(category_frame)
        
        # FAQ items
        for faq in faq_items:
            self._create_faq_item(category_frame, faq)
    
    def _create_faq_item(self, parent: tk.Widget, faq: FAQItem) -> None:
        """Create individual FAQ item."""
        faq_frame = ttk.Frame(parent)
        faq_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Question (clickable)
        question_frame = ttk.Frame(faq_frame)
        question_frame.pack(fill=tk.X)
        
        # Expand/collapse indicator
        indicator_var = tk.StringVar(value="▶")
        indicator_label = ttk.Label(question_frame, textvariable=indicator_var, font=("Segoe UI", 10))
        indicator_label.pack(side=tk.LEFT, padx=(0, 5))
        
        question_label = ttk.Label(
            question_frame,
            text=faq.question,
            font=("Segoe UI", 11, "bold"),
            foreground="#0066cc",
            cursor="hand2"
        )
        question_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Answer (initially hidden)
        answer_frame = ttk.Frame(faq_frame)
        answer_text = tk.Text(
            answer_frame,
            wrap=tk.WORD,
            height=1,  # Will be adjusted based on content
            state=tk.DISABLED,
            font=("Segoe UI", 10),
            bg="#f8f9fa",
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        answer_text.pack(fill=tk.X, padx=(20, 0))
        
        # Configure answer text
        answer_text.config(state=tk.NORMAL)
        answer_text.insert(tk.END, faq.answer)
        answer_text.config(state=tk.DISABLED)
        
        # Calculate required height
        answer_text.update_idletasks()
        lines = int(answer_text.index('end-1c').split('.')[0])
        answer_text.config(height=min(lines, 10))  # Max 10 lines
        
        # Initially hide answer
        answer_frame.pack_forget()
        
        # Toggle function
        def toggle_answer():
            if answer_frame.winfo_viewable():
                answer_frame.pack_forget()
                indicator_var.set("▶")
            else:
                answer_frame.pack(fill=tk.X, pady=(5, 0))
                indicator_var.set("▼")
        
        # Bind click events
        question_label.bind("<Button-1>", lambda e: toggle_answer())
        indicator_label.bind("<Button-1>", lambda e: toggle_answer())
    
    def _update_contact_content(self) -> None:
        """Update contact tab content."""
        if not self.current_content:
            return
        
        # Clear existing content
        for widget in self.contact_details_frame.winfo_children():
            widget.destroy()
        
        contact = self.current_content.contact_info
        
        # Email
        email_frame = ttk.Frame(self.contact_details_frame)
        email_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(email_frame, text="📧 電子郵件:", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        email_label = ttk.Label(
            email_frame, 
            text=contact.email, 
            font=("Segoe UI", 10),
            foreground="#0066cc",
            cursor="hand2"
        )
        email_label.pack(anchor=tk.W, padx=(20, 0))
        email_label.bind("<Button-1>", lambda e: self._open_email(contact.email))
        
        # Support hours
        hours_frame = ttk.Frame(self.contact_details_frame)
        hours_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(hours_frame, text="🕒 支援時間:", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        ttk.Label(hours_frame, text=contact.support_hours, font=("Segoe UI", 10)).pack(anchor=tk.W, padx=(20, 0))
        
        # Response time
        response_frame = ttk.Frame(self.contact_details_frame)
        response_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(response_frame, text="⏱️ 回應時間:", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        ttk.Label(response_frame, text=contact.response_time, font=("Segoe UI", 10)).pack(anchor=tk.W, padx=(20, 0))
        
        # Website
        website_frame = ttk.Frame(self.contact_details_frame)
        website_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(website_frame, text="🌐 網站:", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        website_label = ttk.Label(
            website_frame, 
            text=contact.website, 
            font=("Segoe UI", 10),
            foreground="#0066cc",
            cursor="hand2"
        )
        website_label.pack(anchor=tk.W, padx=(20, 0))
        website_label.bind("<Button-1>", lambda e: self._open_website(contact.website))
    
    def _update_statistics(self) -> None:
        """Update help content statistics."""
        try:
            stats = self.help_storage.get_content_statistics()
            
            stats_text = f"""說明內容統計資訊

📊 內容概覽:
• 常見問題數量: {stats.get('total_faq_items', 0)} 項
• FAQ 分類數量: {stats.get('faq_categories', 0)} 個
• 關於頁面字數: {stats.get('about_word_count', 0):,} 字
• FAQ 總字數: {stats.get('faq_word_count', 0):,} 字
• 總字數: {stats.get('total_word_count', 0):,} 字

📅 版本資訊:
• 內容版本: {stats.get('version', 'N/A')}
• 最後更新: {stats.get('last_updated', 'N/A')[:19] if stats.get('last_updated') else 'N/A'}

📂 分類列表:
{chr(10).join(f'• {cat}' for cat in stats.get('categories', []))}
"""
            
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, stats_text)
            self.stats_text.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"Error updating statistics: {e}")
    
    def _perform_search(self) -> None:
        """Perform search in help content."""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("警告", "請輸入搜尋關鍵字")
            return
        
        try:
            results = self.help_storage.search_content(query)
            self._show_search_results(query, results)
        except Exception as e:
            messagebox.showerror("錯誤", f"搜尋時發生錯誤: {e}")
    
    def _show_search_results(self, query: str, results: List[SearchResult]) -> None:
        """Show search results in a popup window."""
        results_window = tk.Toplevel(self.frame)
        results_window.title(f"搜尋結果: {query}")
        results_window.geometry("600x400")
        results_window.transient(self.frame.winfo_toplevel())
        results_window.grab_set()
        
        # Results header
        header_frame = ttk.Frame(results_window)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            header_frame,
            text=f"搜尋 \"{query}\" 的結果 ({len(results)} 項)",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.W)
        
        if not results:
            ttk.Label(
                header_frame,
                text="沒有找到相關內容",
                font=("Segoe UI", 10),
                foreground="#666666"
            ).pack(anchor=tk.W, pady=(5, 0))
        else:
            # Results list
            results_frame = ttk.Frame(results_window)
            results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
            
            # Create treeview for results
            columns = ("type", "title", "relevance")
            results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=12)
            
            results_tree.heading("type", text="類型")
            results_tree.heading("title", text="標題")
            results_tree.heading("relevance", text="相關性")
            
            results_tree.column("type", width=80, minwidth=60)
            results_tree.column("title", width=300, minwidth=200)
            results_tree.column("relevance", width=80, minwidth=60)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=results_tree.yview)
            results_tree.configure(yscrollcommand=scrollbar.set)
            
            results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Populate results
            type_names = {
                "about": "關於",
                "faq": "FAQ",
                "contact": "聯絡"
            }
            
            for result in results:
                type_name = type_names.get(result.content_type, result.content_type)
                relevance_str = f"{result.relevance_score:.1%}"
                
                item = results_tree.insert("", tk.END, values=(
                    type_name,
                    result.title,
                    relevance_str
                ))
                
                # Store result data
                results_tree.set(item, "#0", result.snippet)
            
            # Show snippet on selection
            snippet_frame = ttk.LabelFrame(results_window, text="內容預覽", padding=10)
            snippet_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            snippet_text = tk.Text(
                snippet_frame,
                height=4,
                wrap=tk.WORD,
                state=tk.DISABLED,
                font=("Segoe UI", 9),
                bg="#f8f9fa"
            )
            snippet_text.pack(fill=tk.X)
            
            def on_select(event):
                selection = results_tree.selection()
                if selection:
                    item = selection[0]
                    snippet = results_tree.set(item, "#0")
                    
                    snippet_text.config(state=tk.NORMAL)
                    snippet_text.delete(1.0, tk.END)
                    snippet_text.insert(tk.END, snippet)
                    snippet_text.config(state=tk.DISABLED)
            
            results_tree.bind("<<TreeviewSelect>>", on_select)
        
        # Close button
        ttk.Button(results_window, text="關閉", command=results_window.destroy).pack(pady=10)
    
    def _clear_search(self) -> None:
        """Clear search input."""
        self.search_var.set("")
    
    def _open_email(self, email: str) -> None:
        """Open email client."""
        try:
            webbrowser.open(f"mailto:{email}")
        except Exception as e:
            messagebox.showerror("錯誤", f"無法開啟電子郵件: {e}")
    
    def _open_website(self, website: str) -> None:
        """Open website in browser."""
        try:
            webbrowser.open(website)
        except Exception as e:
            messagebox.showerror("錯誤", f"無法開啟網站: {e}")
    
    def refresh_content(self) -> None:
        """Refresh page content (called on each activation)."""
        self._load_help_content()