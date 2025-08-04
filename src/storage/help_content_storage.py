"""
Help content storage implementation for Windows Scheduler GUI.
"""

import json
import os
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging

from src.models.help_models import HelpContent, FAQItem, ContactInfo, SearchResult
from src.utils.constants import DATA_DIR, HELP_CONTENT_FILE, APP_VERSION


class HelpContentStorage:
    """Storage for help content, FAQ items, and contact information."""
    
    def __init__(self, data_dir: str = DATA_DIR, content_file: str = HELP_CONTENT_FILE):
        """
        Initialize help content storage.
        
        Args:
            data_dir: Directory for data files
            content_file: Help content file name
        """
        self.data_dir = Path(data_dir)
        self.content_file = content_file
        self.content_path = self.data_dir / content_file
        self.assets_dir = self.data_dir / "help_assets"
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Cached content
        self._cached_content: Optional[HelpContent] = None
        self._cache_timestamp: Optional[datetime] = None
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Load or create default content
        self._initialize_content()
    
    def _ensure_directories(self) -> None:
        """Ensure data and assets directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
    
    def _initialize_content(self) -> None:
        """Initialize help content with defaults if not exists."""
        if not self.content_path.exists():
            default_content = self.get_default_content()
            self.save_help_content(default_content)
            self.logger.info("Created default help content")
    
    def load_help_content(self) -> HelpContent:
        """
        Load help content from storage.
        
        Returns:
            HelpContent object
        """
        with self._lock:
            try:
                # Check if we can use cached content
                if self._cached_content and self._cache_timestamp:
                    file_mtime = datetime.fromtimestamp(self.content_path.stat().st_mtime)
                    if file_mtime <= self._cache_timestamp:
                        return self._cached_content
                
                # Load from file
                if not self.content_path.exists():
                    self.logger.warning("Help content file not found, using defaults")
                    return self.get_default_content()
                
                with open(self.content_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                content = HelpContent.from_dict(data)
                
                # Update cache
                self._cached_content = content
                self._cache_timestamp = datetime.now()
                
                self.logger.info("Help content loaded successfully")
                return content
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in help content file: {e}")
                return self.get_default_content()
            except Exception as e:
                self.logger.error(f"Error loading help content: {e}")
                return self.get_default_content()
    
    def save_help_content(self, content: HelpContent) -> bool:
        """
        Save help content to storage.
        
        Args:
            content: HelpContent to save
            
        Returns:
            True if save was successful
        """
        with self._lock:
            try:
                # Update last modified timestamp
                content.last_updated = datetime.now()
                
                # Convert to dictionary
                data = content.to_dict()
                
                # Create backup if file exists
                if self.content_path.exists():
                    backup_path = self.content_path.with_suffix('.bak')
                    self.content_path.rename(backup_path)
                
                # Write new content
                with open(self.content_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Remove backup if successful
                backup_path = self.content_path.with_suffix('.bak')
                if backup_path.exists():
                    backup_path.unlink()
                
                # Update cache
                self._cached_content = content
                self._cache_timestamp = datetime.now()
                
                self.logger.info("Help content saved successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error saving help content: {e}")
                
                # Restore backup if it exists
                backup_path = self.content_path.with_suffix('.bak')
                if backup_path.exists():
                    backup_path.rename(self.content_path)
                
                return False
    
    def get_default_content(self) -> HelpContent:
        """
        Get default help content.
        
        Returns:
            Default HelpContent object
        """
        # Default about text
        about_text = f"""# Windows 排程控制 GUI

歡迎使用 Windows 排程控制 GUI！這是一個功能強大的應用程式，讓您能夠輕鬆管理和自動化 Windows 應用程式的操作。

## 主要功能

### 📅 排程管理
- 建立和編輯自動化任務
- 支援多種觸發時間設定
- 靈活的排程配置選項

### 🖥️ Windows 控制
- 啟動和關閉應用程式
- 調整視窗大小和位置
- 發送鍵盤和滑鼠操作

### 📊 監控和日誌
- 即時任務執行狀態
- 詳細的執行歷史記錄
- 豐富的統計資訊

### ⚙️ 系統設定
- 個人化介面設定
- 通知和日誌配置
- 匯入/匯出設定

## 快速開始

1. **建立第一個任務**: 點擊「Schedules」頁面的「新增任務」按鈕
2. **設定排程**: 選擇觸發時間和重複頻率
3. **選擇操作**: 指定要執行的 Windows 操作
4. **啟動排程器**: 在「Overview」頁面啟動自動執行

## 版本資訊

版本: {APP_VERSION}
最後更新: {datetime.now().strftime('%Y-%m-%d')}

感謝您使用我們的軟體！如有任何問題，請參考常見問題或聯絡我們的支援團隊。
"""
        
        # Default FAQ items
        faq_items = [
            FAQItem(
                id="faq_001",
                question="如何建立我的第一個排程任務？",
                answer="""建立排程任務很簡單：

1. 點擊導航列的「Schedules」進入排程管理頁面
2. 點擊「新增任務」按鈕
3. 填寫任務名稱和描述
4. 選擇目標應用程式
5. 設定要執行的操作（啟動、關閉、調整視窗等）
6. 配置觸發時間和重複頻率
7. 點擊「儲存」完成建立

建立完成後，任務會出現在排程清單中，您可以隨時編輯或刪除。""",
                category="基本操作",
                order=1
            ),
            FAQItem(
                id="faq_002",
                question="支援哪些類型的 Windows 操作？",
                answer="""系統支援多種 Windows 操作：

**應用程式控制：**
- 啟動應用程式
- 關閉應用程式
- 強制結束程序

**視窗操作：**
- 調整視窗大小
- 移動視窗位置
- 最小化/最大化視窗
- 設定視窗焦點

**輸入操作：**
- 發送鍵盤快捷鍵
- 模擬滑鼠點擊
- 輸入文字內容

**系統操作：**
- 執行 PowerShell 命令
- 檔案和資料夾操作

每種操作都有詳細的參數設定，讓您精確控制執行行為。""",
                category="功能說明",
                order=2
            ),
            FAQItem(
                id="faq_003",
                question="如何設定排程的觸發時間？",
                answer="""系統提供多種觸發時間選項：

**一次性執行：**
- 指定具體的日期和時間
- 適合單次任務

**重複執行：**
- 每日：設定每天的執行時間
- 每週：選擇星期幾和時間
- 每月：指定日期和時間
- 自訂間隔：設定分鐘、小時或天數間隔

**條件觸發：**
- 當特定應用程式啟動時
- 當系統空閒時
- 當檔案變更時

您可以組合多種觸發條件，創建複雜的自動化流程。""",
                category="排程設定",
                order=3
            ),
            FAQItem(
                id="faq_004",
                question="如何查看任務執行歷史？",
                answer="""查看執行歷史有多種方式：

**日誌頁面：**
1. 點擊「Logs」進入執行記錄頁面
2. 使用搜尋和篩選功能找到特定記錄
3. 雙擊記錄查看詳細資訊

**概覽頁面：**
- 顯示最近的執行活動
- 提供執行統計摘要

**排程頁面：**
- 每個任務顯示最後執行時間
- 顯示執行狀態（成功/失敗）

**匯出功能：**
- 支援匯出為 JSON、CSV、TXT 格式
- 可選擇時間範圍和篩選條件""",
                category="監控日誌",
                order=4
            ),
            FAQItem(
                id="faq_005",
                question="系統設定可以備份和還原嗎？",
                answer="""是的，系統提供完整的備份和還原功能：

**自動備份：**
- 系統會自動建立設定備份
- 保留最近 10 個備份檔案
- 支援設定變更時的增量備份

**手動匯出：**
1. 進入「Settings」設定頁面
2. 點擊「匯出設定」按鈕
3. 選擇儲存位置和檔案名稱

**匯入還原：**
1. 點擊「匯入設定」按鈕
2. 選擇之前匯出的設定檔案
3. 確認匯入後重新啟動應用程式

**包含內容：**
- 所有系統設定選項
- 介面偏好設定
- 通知和日誌配置
- 不包含任務資料（需另外備份）""",
                category="系統設定",
                order=5
            ),
            FAQItem(
                id="faq_006",
                question="遇到錯誤時該怎麼辦？",
                answer="""遇到問題時請按照以下步驟：

**檢查日誌：**
1. 查看「Logs」頁面的錯誤記錄
2. 注意錯誤訊息和時間
3. 檢查是否有重複發生的問題

**常見解決方法：**
- 確認目標應用程式已安裝且可正常啟動
- 檢查 Windows 權限設定
- 重新啟動應用程式
- 檢查系統資源使用情況

**重設設定：**
- 如果問題持續，可嘗試重設為預設設定
- 在設定頁面點擊「重設為預設值」

**聯絡支援：**
- 如果問題無法解決，請聯絡我們的技術支援
- 提供錯誤日誌和問題描述
- 我們會在 24 小時內回覆""",
                category="故障排除",
                order=6
            )
        ]
        
        # Default contact info
        contact_info = ContactInfo(
            email="support@windows-scheduler-gui.com",
            support_hours="週一至週五 09:00-18:00 (GMT+8)",
            response_time="24 小時內回覆",
            website="https://github.com/windows-scheduler-gui"
        )
        
        return HelpContent(
            about_text=about_text,
            faq_items=faq_items,
            contact_info=contact_info,
            version=APP_VERSION,
            last_updated=datetime.now()
        )
    
    def load_faq_items(self) -> List[FAQItem]:
        """
        Load FAQ items from help content.
        
        Returns:
            List of FAQItem objects
        """
        content = self.load_help_content()
        return content.faq_items
    
    def save_faq_items(self, items: List[FAQItem]) -> bool:
        """
        Save FAQ items to help content.
        
        Args:
            items: List of FAQItem objects
            
        Returns:
            True if save was successful
        """
        try:
            content = self.load_help_content()
            content.faq_items = items
            content.last_updated = datetime.now()
            return self.save_help_content(content)
        except Exception as e:
            self.logger.error(f"Error saving FAQ items: {e}")
            return False
    
    def load_contact_info(self) -> ContactInfo:
        """
        Load contact information from help content.
        
        Returns:
            ContactInfo object
        """
        content = self.load_help_content()
        return content.contact_info
    
    def save_contact_info(self, contact_info: ContactInfo) -> bool:
        """
        Save contact information to help content.
        
        Args:
            contact_info: ContactInfo object
            
        Returns:
            True if save was successful
        """
        try:
            content = self.load_help_content()
            content.contact_info = contact_info
            content.last_updated = datetime.now()
            return self.save_help_content(content)
        except Exception as e:
            self.logger.error(f"Error saving contact info: {e}")
            return False
    
    def search_content(self, query: str) -> List[SearchResult]:
        """
        Search help content for a query.
        
        Args:
            query: Search query string
            
        Returns:
            List of SearchResult objects
        """
        if not query.strip():
            return []
        
        try:
            content = self.load_help_content()
            results = []
            query_lower = query.lower()
            
            # Search in about text
            about_lines = content.about_text.split('\n')
            for i, line in enumerate(about_lines):
                if query_lower in line.lower():
                    # Calculate relevance score
                    relevance = self._calculate_relevance(query_lower, line.lower())
                    
                    # Create snippet
                    snippet = self._create_snippet(about_lines, i, query)
                    
                    results.append(SearchResult(
                        content_type="about",
                        title="關於應用程式",
                        snippet=snippet,
                        relevance_score=relevance
                    ))
            
            # Search in FAQ items
            for faq in content.faq_items:
                question_match = query_lower in faq.question.lower()
                answer_match = query_lower in faq.answer.lower()
                
                if question_match or answer_match:
                    # Calculate relevance (question matches are more relevant)
                    relevance = 0.0
                    if question_match:
                        relevance += self._calculate_relevance(query_lower, faq.question.lower()) * 2
                    if answer_match:
                        relevance += self._calculate_relevance(query_lower, faq.answer.lower())
                    
                    # Create snippet
                    if question_match:
                        snippet = faq.question
                    else:
                        snippet = self._create_text_snippet(faq.answer, query)
                    
                    results.append(SearchResult(
                        content_type="faq",
                        title=faq.question,
                        snippet=snippet,
                        relevance_score=relevance
                    ))
            
            # Search in contact info
            contact_text = f"{content.contact_info.email} {content.contact_info.support_hours} {content.contact_info.response_time}"
            if query_lower in contact_text.lower():
                relevance = self._calculate_relevance(query_lower, contact_text.lower())
                
                results.append(SearchResult(
                    content_type="contact",
                    title="聯絡資訊",
                    snippet=f"Email: {content.contact_info.email}",
                    relevance_score=relevance
                ))
            
            # Sort by relevance score (highest first)
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching help content: {e}")
            return []
    
    def _calculate_relevance(self, query: str, text: str) -> float:
        """
        Calculate relevance score for search results.
        
        Args:
            query: Search query (lowercase)
            text: Text to search in (lowercase)
            
        Returns:
            Relevance score between 0 and 1
        """
        if not query or not text:
            return 0.0
        
        # Count exact matches
        exact_matches = text.count(query)
        
        # Count word matches
        query_words = query.split()
        text_words = text.split()
        word_matches = sum(1 for word in query_words if word in text_words)
        
        # Calculate score
        exact_score = exact_matches * 0.6
        word_score = (word_matches / len(query_words)) * 0.4 if query_words else 0
        
        return min(exact_score + word_score, 1.0)
    
    def _create_snippet(self, lines: List[str], match_line: int, query: str) -> str:
        """
        Create a snippet around the matching line.
        
        Args:
            lines: All lines of text
            match_line: Index of matching line
            query: Search query
            
        Returns:
            Snippet string
        """
        start = max(0, match_line - 1)
        end = min(len(lines), match_line + 2)
        
        snippet_lines = lines[start:end]
        snippet = ' '.join(line.strip() for line in snippet_lines if line.strip())
        
        # Limit snippet length
        if len(snippet) > 150:
            snippet = snippet[:147] + "..."
        
        return snippet
    
    def _create_text_snippet(self, text: str, query: str) -> str:
        """
        Create a snippet from text around the query match.
        
        Args:
            text: Full text
            query: Search query
            
        Returns:
            Snippet string
        """
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Find first occurrence
        match_pos = text_lower.find(query_lower)
        if match_pos == -1:
            return text[:150] + "..." if len(text) > 150 else text
        
        # Create snippet around match
        start = max(0, match_pos - 50)
        end = min(len(text), match_pos + len(query) + 50)
        
        snippet = text[start:end]
        
        # Add ellipsis if needed
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    def add_faq_item(self, faq_item: FAQItem) -> bool:
        """
        Add a new FAQ item.
        
        Args:
            faq_item: FAQItem to add
            
        Returns:
            True if add was successful
        """
        try:
            faq_items = self.load_faq_items()
            
            # Check for duplicate ID
            if any(item.id == faq_item.id for item in faq_items):
                self.logger.warning(f"FAQ item with ID {faq_item.id} already exists")
                return False
            
            faq_items.append(faq_item)
            return self.save_faq_items(faq_items)
            
        except Exception as e:
            self.logger.error(f"Error adding FAQ item: {e}")
            return False
    
    def update_faq_item(self, faq_item: FAQItem) -> bool:
        """
        Update an existing FAQ item.
        
        Args:
            faq_item: FAQItem with updated data
            
        Returns:
            True if update was successful
        """
        try:
            faq_items = self.load_faq_items()
            
            # Find and update the item
            for i, item in enumerate(faq_items):
                if item.id == faq_item.id:
                    faq_items[i] = faq_item
                    return self.save_faq_items(faq_items)
            
            self.logger.warning(f"FAQ item with ID {faq_item.id} not found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating FAQ item: {e}")
            return False
    
    def delete_faq_item(self, faq_id: str) -> bool:
        """
        Delete an FAQ item by ID.
        
        Args:
            faq_id: ID of FAQ item to delete
            
        Returns:
            True if delete was successful
        """
        try:
            faq_items = self.load_faq_items()
            
            # Find and remove the item
            original_count = len(faq_items)
            faq_items = [item for item in faq_items if item.id != faq_id]
            
            if len(faq_items) == original_count:
                self.logger.warning(f"FAQ item with ID {faq_id} not found")
                return False
            
            return self.save_faq_items(faq_items)
            
        except Exception as e:
            self.logger.error(f"Error deleting FAQ item: {e}")
            return False
    
    def get_faq_categories(self) -> List[str]:
        """
        Get list of FAQ categories.
        
        Returns:
            List of category names
        """
        try:
            faq_items = self.load_faq_items()
            categories = list(set(item.category for item in faq_items))
            return sorted(categories)
        except Exception as e:
            self.logger.error(f"Error getting FAQ categories: {e}")
            return []
    
    def get_faq_by_category(self, category: str) -> List[FAQItem]:
        """
        Get FAQ items by category.
        
        Args:
            category: Category name
            
        Returns:
            List of FAQItem objects in the category
        """
        try:
            faq_items = self.load_faq_items()
            category_items = [item for item in faq_items if item.category == category]
            return sorted(category_items, key=lambda x: x.order)
        except Exception as e:
            self.logger.error(f"Error getting FAQ by category: {e}")
            return []
    
    def export_help_content(self, file_path: Union[str, Path]) -> bool:
        """
        Export help content to a file.
        
        Args:
            file_path: Path to export file
            
        Returns:
            True if export was successful
        """
        try:
            content = self.load_help_content()
            
            export_data = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "version": content.version,
                    "application": "Windows Scheduler GUI"
                },
                "help_content": content.to_dict()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Help content exported to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting help content: {e}")
            return False
    
    def import_help_content(self, file_path: Union[str, Path]) -> bool:
        """
        Import help content from a file.
        
        Args:
            file_path: Path to import file
            
        Returns:
            True if import was successful
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Extract help content data
            if "help_content" in import_data:
                content_data = import_data["help_content"]
            else:
                # Assume entire file is help content
                content_data = import_data
            
            # Create and validate help content
            content = HelpContent.from_dict(content_data)
            
            # Save imported content
            success = self.save_help_content(content)
            
            if success:
                self.logger.info(f"Help content imported from {file_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error importing help content: {e}")
            return False
    
    def get_content_statistics(self) -> Dict[str, Any]:
        """
        Get help content statistics.
        
        Returns:
            Dictionary containing content statistics
        """
        try:
            content = self.load_help_content()
            
            # Calculate statistics
            total_faq = len(content.faq_items)
            categories = self.get_faq_categories()
            
            # Count words in about text
            about_words = len(content.about_text.split())
            
            # Calculate total FAQ words
            faq_words = sum(len(f"{item.question} {item.answer}".split()) for item in content.faq_items)
            
            return {
                "total_faq_items": total_faq,
                "faq_categories": len(categories),
                "about_word_count": about_words,
                "faq_word_count": faq_words,
                "total_word_count": about_words + faq_words,
                "last_updated": content.last_updated.isoformat(),
                "version": content.version,
                "categories": categories
            }
            
        except Exception as e:
            self.logger.error(f"Error getting content statistics: {e}")
            return {}
    
    def clear_cache(self) -> None:
        """Clear the content cache."""
        with self._lock:
            self._cached_content = None
            self._cache_timestamp = None


# Global help content storage instance
_help_content_storage: Optional[HelpContentStorage] = None


def get_help_content_storage() -> HelpContentStorage:
    """
    Get the global help content storage instance.
    
    Returns:
        HelpContentStorage instance
    """
    global _help_content_storage
    if _help_content_storage is None:
        _help_content_storage = HelpContentStorage()
    return _help_content_storage


def initialize_help_content_storage(data_dir: Optional[str] = None, content_file: Optional[str] = None) -> HelpContentStorage:
    """
    Initialize the global help content storage.
    
    Args:
        data_dir: Optional custom data directory
        content_file: Optional custom content file name
        
    Returns:
        HelpContentStorage instance
    """
    global _help_content_storage
    if data_dir or content_file:
        _help_content_storage = HelpContentStorage(
            data_dir=data_dir or DATA_DIR,
            content_file=content_file or HELP_CONTENT_FILE
        )
    else:
        _help_content_storage = HelpContentStorage()
    return _help_content_storage