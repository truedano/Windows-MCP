"""
Help content management system for Windows Scheduler GUI.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from src.models.help_models import HelpContent, FAQItem, ContactInfo, SearchResult
from src.storage.help_content_storage import HelpContentStorage, get_help_content_storage


class HelpContentManager:
    """
    Central help content management system.
    
    Provides help content loading, searching, and management functionality.
    """
    
    def __init__(self, storage: Optional[HelpContentStorage] = None):
        """
        Initialize help content manager.
        
        Args:
            storage: Help content storage instance
        """
        self.storage = storage or get_help_content_storage()
        self._content: Optional[HelpContent] = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load initial content
        self._load_initial_content()
    
    def _load_initial_content(self):
        """Load initial help content on startup."""
        try:
            self._content = self.storage.load_help_content()
            if self._content:
                self.logger.info("Help content loaded successfully")
            else:
                self.logger.warning("No help content found, using default content")
                self._content = self._get_default_content()
                # Save default content
                self.update_content(self._content)
                
        except Exception as e:
            self.logger.error(f"Error loading initial help content: {e}")
            self._content = self._get_default_content()
    
    def load_help_content(self) -> HelpContent:
        """
        Load help content from storage.
        
        Returns:
            HelpContent instance
        """
        try:
            content = self.storage.load_help_content()
            if content:
                self._content = content
                self.logger.info("Help content reloaded from storage")
            else:
                self.logger.warning("No help content found in storage")
                if not self._content:
                    self._content = self._get_default_content()
            
            return self._content
            
        except Exception as e:
            self.logger.error(f"Error loading help content: {e}")
            if not self._content:
                self._content = self._get_default_content()
            return self._content
    
    def get_about_content(self) -> str:
        """
        Get the about section content.
        
        Returns:
            About text content
        """
        if not self._content:
            self.load_help_content()
        return self._content.about_text if self._content else ""
    
    def get_faq_items(self, category: Optional[str] = None) -> List[FAQItem]:
        """
        Get FAQ items, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of FAQ items
        """
        if not self._content:
            self.load_help_content()
        
        if not self._content:
            return []
        
        faq_items = self._content.faq_items
        
        # Filter by category if specified
        if category:
            faq_items = [item for item in faq_items if item.category.lower() == category.lower()]
        
        # Sort by order
        faq_items.sort(key=lambda x: x.order)
        
        return faq_items
    
    def get_faq_categories(self) -> List[str]:
        """
        Get all available FAQ categories.
        
        Returns:
            List of unique categories
        """
        if not self._content:
            self.load_help_content()
        
        if not self._content:
            return []
        
        categories = list(set(item.category for item in self._content.faq_items))
        categories.sort()
        return categories
    
    def get_faq_item_by_id(self, faq_id: str) -> Optional[FAQItem]:
        """
        Get a specific FAQ item by ID.
        
        Args:
            faq_id: FAQ item ID
            
        Returns:
            FAQ item or None if not found
        """
        if not self._content:
            self.load_help_content()
        
        if not self._content:
            return None
        
        for item in self._content.faq_items:
            if item.id == faq_id:
                return item
        
        return None
    
    def search_content(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search help content for the given query.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        if not self._content:
            self.load_help_content()
        
        if not self._content or not query.strip():
            return []
        
        query = query.strip().lower()
        results = []
        
        # Search in about content
        about_score = self._calculate_relevance_score(query, self._content.about_text)
        if about_score > 0:
            snippet = self._extract_snippet(self._content.about_text, query)
            results.append(SearchResult(
                content_type="about",
                title="關於應用程式",
                snippet=snippet,
                relevance_score=about_score
            ))
        
        # Search in FAQ items
        for faq_item in self._content.faq_items:
            # Search in question
            question_score = self._calculate_relevance_score(query, faq_item.question)
            answer_score = self._calculate_relevance_score(query, faq_item.answer)
            
            total_score = max(question_score, answer_score * 0.8)  # Weight question higher
            
            if total_score > 0:
                # Use question as snippet if it matches, otherwise extract from answer
                if question_score > answer_score:
                    snippet = faq_item.question
                else:
                    snippet = self._extract_snippet(faq_item.answer, query)
                
                results.append(SearchResult(
                    content_type="faq",
                    title=faq_item.question,
                    snippet=snippet,
                    relevance_score=total_score
                ))
        
        # Search in contact info
        contact_text = f"{self._content.contact_info.email} {self._content.contact_info.support_hours} {self._content.contact_info.response_time}"
        contact_score = self._calculate_relevance_score(query, contact_text)
        if contact_score > 0:
            snippet = self._extract_snippet(contact_text, query)
            results.append(SearchResult(
                content_type="contact",
                title="聯絡資訊",
                snippet=snippet,
                relevance_score=contact_score
            ))
        
        # Sort by relevance score (descending) and limit results
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:max_results]
    
    def get_contact_info(self) -> ContactInfo:
        """
        Get contact information.
        
        Returns:
            ContactInfo instance
        """
        if not self._content:
            self.load_help_content()
        
        return self._content.contact_info if self._content else ContactInfo(
            email="support@example.com",
            support_hours="週一至週五 9:00-18:00",
            response_time="24小時內回覆",
            website="https://example.com"
        )
    
    def update_content(self, content: HelpContent) -> bool:
        """
        Update help content.
        
        Args:
            content: New help content
            
        Returns:
            True if update was successful
        """
        try:
            # Update timestamp
            content.last_updated = datetime.now()
            
            # Save to storage
            success = self.storage.save_help_content(content)
            
            if success:
                self._content = content
                self.logger.info("Help content updated successfully")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error updating help content: {e}")
            return False
    
    def add_faq_item(self, question: str, answer: str, category: str) -> bool:
        """
        Add a new FAQ item.
        
        Args:
            question: FAQ question
            answer: FAQ answer
            category: FAQ category
            
        Returns:
            True if addition was successful
        """
        try:
            if not self._content:
                self.load_help_content()
            
            if not self._content:
                return False
            
            # Generate new ID
            existing_ids = [item.id for item in self._content.faq_items]
            new_id = self._generate_faq_id(existing_ids)
            
            # Determine order (last in category)
            category_items = [item for item in self._content.faq_items if item.category == category]
            order = max([item.order for item in category_items], default=0) + 1
            
            # Create new FAQ item
            new_item = FAQItem(
                id=new_id,
                question=question,
                answer=answer,
                category=category,
                order=order
            )
            
            # Add to content
            self._content.faq_items.append(new_item)
            
            # Save updated content
            return self.update_content(self._content)
            
        except Exception as e:
            self.logger.error(f"Error adding FAQ item: {e}")
            return False
    
    def update_faq_item(self, faq_id: str, question: Optional[str] = None, 
                       answer: Optional[str] = None, category: Optional[str] = None) -> bool:
        """
        Update an existing FAQ item.
        
        Args:
            faq_id: FAQ item ID
            question: New question (optional)
            answer: New answer (optional)
            category: New category (optional)
            
        Returns:
            True if update was successful
        """
        try:
            if not self._content:
                self.load_help_content()
            
            if not self._content:
                return False
            
            # Find the FAQ item
            for item in self._content.faq_items:
                if item.id == faq_id:
                    if question is not None:
                        item.question = question
                    if answer is not None:
                        item.answer = answer
                    if category is not None:
                        item.category = category
                    
                    # Save updated content
                    return self.update_content(self._content)
            
            self.logger.warning(f"FAQ item with ID '{faq_id}' not found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating FAQ item: {e}")
            return False
    
    def delete_faq_item(self, faq_id: str) -> bool:
        """
        Delete an FAQ item.
        
        Args:
            faq_id: FAQ item ID
            
        Returns:
            True if deletion was successful
        """
        try:
            if not self._content:
                self.load_help_content()
            
            if not self._content:
                return False
            
            # Find and remove the FAQ item
            original_count = len(self._content.faq_items)
            self._content.faq_items = [item for item in self._content.faq_items if item.id != faq_id]
            
            if len(self._content.faq_items) < original_count:
                # Save updated content
                return self.update_content(self._content)
            else:
                self.logger.warning(f"FAQ item with ID '{faq_id}' not found")
                return False
            
        except Exception as e:
            self.logger.error(f"Error deleting FAQ item: {e}")
            return False
    
    def get_content_version(self) -> str:
        """
        Get the current content version.
        
        Returns:
            Content version string
        """
        if not self._content:
            self.load_help_content()
        
        return self._content.version if self._content else "1.0"
    
    def get_last_updated(self) -> datetime:
        """
        Get the last updated timestamp.
        
        Returns:
            Last updated datetime
        """
        if not self._content:
            self.load_help_content()
        
        return self._content.last_updated if self._content else datetime.now()
    
    def _calculate_relevance_score(self, query: str, text: str) -> float:
        """
        Calculate relevance score for search query in text.
        
        Args:
            query: Search query
            text: Text to search in
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        if not query or not text:
            return 0.0
        
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Exact match gets highest score
        if query_lower in text_lower:
            # Calculate position-based score (earlier matches score higher)
            position = text_lower.find(query_lower)
            position_score = 1.0 - (position / len(text_lower))
            
            # Calculate length-based score (shorter text with match scores higher)
            length_score = min(1.0, 100.0 / len(text_lower))
            
            return min(1.0, 0.7 + position_score * 0.2 + length_score * 0.1)
        
        # Partial word matches
        query_words = query_lower.split()
        text_words = text_lower.split()
        
        matches = 0
        for query_word in query_words:
            for text_word in text_words:
                if query_word in text_word or text_word in query_word:
                    matches += 1
                    break
        
        if matches > 0:
            return min(0.6, matches / len(query_words) * 0.6)
        
        return 0.0
    
    def _extract_snippet(self, text: str, query: str, max_length: int = 150) -> str:
        """
        Extract a snippet from text around the query match.
        
        Args:
            text: Source text
            query: Search query
            max_length: Maximum snippet length
            
        Returns:
            Text snippet
        """
        if not query or not text:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Find the position of the query in the text
        position = text_lower.find(query_lower)
        
        if position == -1:
            # Query not found, return beginning of text
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # Calculate snippet boundaries
        start = max(0, position - max_length // 3)
        end = min(len(text), start + max_length)
        
        # Adjust start if end reached text boundary
        if end == len(text):
            start = max(0, end - max_length)
        
        snippet = text[start:end]
        
        # Add ellipsis if needed
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    def _generate_faq_id(self, existing_ids: List[str]) -> str:
        """
        Generate a unique FAQ ID.
        
        Args:
            existing_ids: List of existing FAQ IDs
            
        Returns:
            New unique FAQ ID
        """
        base_id = "faq"
        counter = 1
        
        while f"{base_id}_{counter:03d}" in existing_ids:
            counter += 1
        
        return f"{base_id}_{counter:03d}"
    
    def _get_default_content(self) -> HelpContent:
        """
        Get default help content.
        
        Returns:
            Default HelpContent instance
        """
        default_about = """
# Windows 排程控制 GUI

Windows 排程控制 GUI 是一個基於 Python Tkinter 的應用程式，用於管理和自動化 Windows 應用程式的操作。

## 主要功能

- **排程管理**: 建立、編輯和刪除應用程式排程任務
- **應用程式控制**: 啟動、關閉、調整視窗大小和位置
- **執行監控**: 即時監控任務執行狀態和結果
- **日誌記錄**: 詳細的執行歷史和錯誤記錄
- **系統設定**: 靈活的配置選項和個人化設定

## 系統需求

- Windows 7 或更新版本
- Python 3.13+
- 足夠的系統權限執行應用程式操作

## 開始使用

1. 啟動應用程式
2. 在「排程」頁面建立新的排程任務
3. 設定目標應用程式和執行時間
4. 選擇要執行的操作類型
5. 儲存並啟用排程

更多詳細資訊請參考常見問題或聯絡技術支援。
        """.strip()
        
        default_faq_items = [
            FAQItem(
                id="faq_001",
                question="如何建立新的排程任務？",
                answer="1. 點擊導航列的「排程」\n2. 點擊「新增排程」按鈕\n3. 填寫任務名稱和描述\n4. 選擇目標應用程式\n5. 設定執行時間和重複選項\n6. 選擇要執行的操作\n7. 點擊「儲存」完成建立",
                category="基本操作",
                order=1
            ),
            FAQItem(
                id="faq_002",
                question="支援哪些應用程式操作？",
                answer="系統支援以下操作：\n- 啟動應用程式\n- 關閉應用程式\n- 調整視窗大小\n- 移動視窗位置\n- 最小化/最大化視窗\n- 點擊視窗元素\n- 輸入文字\n- 發送快捷鍵\n- 執行自訂 PowerShell 命令",
                category="功能說明",
                order=1
            ),
            FAQItem(
                id="faq_003",
                question="如何查看任務執行記錄？",
                answer="1. 點擊導航列的「記錄」\n2. 在記錄頁面可以看到所有執行歷史\n3. 使用搜尋功能快速找到特定記錄\n4. 點擊記錄項目查看詳細資訊\n5. 可以按時間、狀態等條件篩選記錄",
                category="基本操作",
                order=2
            ),
            FAQItem(
                id="faq_004",
                question="任務執行失敗怎麼辦？",
                answer="如果任務執行失敗：\n1. 檢查目標應用程式是否正常運行\n2. 確認操作參數是否正確\n3. 查看錯誤記錄了解具體原因\n4. 檢查系統權限是否足夠\n5. 嘗試手動執行相同操作\n6. 如問題持續，請聯絡技術支援",
                category="故障排除",
                order=1
            ),
            FAQItem(
                id="faq_005",
                question="如何修改系統設定？",
                answer="1. 點擊導航列的「設定」\n2. 在設定頁面可以調整：\n   - 排程檢查頻率\n   - 通知選項\n   - 日誌保留期限\n   - 介面主題\n   - 語言設定\n3. 修改後點擊「儲存」套用變更\n4. 部分設定可能需要重新啟動應用程式",
                category="基本操作",
                order=3
            ),
            FAQItem(
                id="faq_006",
                question="系統安全性如何保障？",
                answer="系統採用多重安全措施：\n- 危險操作需要使用者確認\n- 限制系統存取權限\n- 記錄所有操作以供審計\n- 驗證操作參數的安全性\n- 提供操作回復機制\n- 定期備份重要資料",
                category="安全性",
                order=1
            )
        ]
        
        default_contact_info = ContactInfo(
            email="support@windows-scheduler-gui.com",
            support_hours="週一至週五 9:00-18:00 (GMT+8)",
            response_time="24小時內回覆",
            website="https://github.com/windows-scheduler-gui"
        )
        
        return HelpContent(
            about_text=default_about,
            faq_items=default_faq_items,
            contact_info=default_contact_info,
            version="1.0",
            last_updated=datetime.now()
        )


# Global help content manager instance
_help_content_manager: Optional[HelpContentManager] = None


def get_help_content_manager() -> HelpContentManager:
    """
    Get the global help content manager instance.
    
    Returns:
        HelpContentManager instance
    """
    global _help_content_manager
    if _help_content_manager is None:
        _help_content_manager = HelpContentManager()
    return _help_content_manager


def initialize_help_content_manager(storage: Optional[HelpContentStorage] = None) -> HelpContentManager:
    """
    Initialize the global help content manager.
    
    Args:
        storage: Optional custom storage instance
        
    Returns:
        HelpContentManager instance
    """
    global _help_content_manager
    _help_content_manager = HelpContentManager(storage)
    return _help_content_manager