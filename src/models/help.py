"""
Help content and support models.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class FAQItem:
    """Frequently Asked Question item."""
    id: str
    question: str
    answer: str
    category: str
    order: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'order': self.order
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FAQItem':
        """Create instance from dictionary."""
        return cls(
            id=data['id'],
            question=data['question'],
            answer=data['answer'],
            category=data['category'],
            order=data['order']
        )


@dataclass
class ContactInfo:
    """Contact information for support."""
    email: str
    support_hours: str
    response_time: str
    website: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'email': self.email,
            'support_hours': self.support_hours,
            'response_time': self.response_time,
            'website': self.website
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContactInfo':
        """Create instance from dictionary."""
        return cls(
            email=data['email'],
            support_hours=data['support_hours'],
            response_time=data['response_time'],
            website=data['website']
        )


@dataclass
class SearchResult:
    """Search result for help content."""
    content_type: str  # "about", "faq", "contact"
    title: str
    snippet: str
    relevance_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'content_type': self.content_type,
            'title': self.title,
            'snippet': self.snippet,
            'relevance_score': self.relevance_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """Create instance from dictionary."""
        return cls(
            content_type=data['content_type'],
            title=data['title'],
            snippet=data['snippet'],
            relevance_score=data['relevance_score']
        )


@dataclass
class HelpContent:
    """Complete help content structure."""
    about_text: str
    faq_items: List[FAQItem]
    contact_info: ContactInfo
    version: str
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'about_text': self.about_text,
            'faq_items': [item.to_dict() for item in self.faq_items],
            'contact_info': self.contact_info.to_dict(),
            'version': self.version,
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HelpContent':
        """Create instance from dictionary."""
        return cls(
            about_text=data['about_text'],
            faq_items=[FAQItem.from_dict(item) for item in data['faq_items']],
            contact_info=ContactInfo.from_dict(data['contact_info']),
            version=data['version'],
            last_updated=datetime.fromisoformat(data['last_updated'])
        )
    
    def get_faq_by_category(self, category: str) -> List[FAQItem]:
        """Get FAQ items by category."""
        return [item for item in self.faq_items if item.category == category]
    
    def search_content(self, query: str) -> List[SearchResult]:
        """
        Search through help content.
        
        Args:
            query: Search query string
            
        Returns:
            List[SearchResult]: Matching search results
        """
        results = []
        query_lower = query.lower()
        
        # Search in about text
        if query_lower in self.about_text.lower():
            snippet = self._extract_snippet(self.about_text, query_lower)
            results.append(SearchResult(
                content_type="about",
                title="關於應用程式",
                snippet=snippet,
                relevance_score=self._calculate_relevance(self.about_text, query_lower)
            ))
        
        # Search in FAQ items
        for faq in self.faq_items:
            question_match = query_lower in faq.question.lower()
            answer_match = query_lower in faq.answer.lower()
            
            if question_match or answer_match:
                snippet = faq.question if question_match else self._extract_snippet(faq.answer, query_lower)
                relevance = self._calculate_relevance(faq.question + " " + faq.answer, query_lower)
                
                results.append(SearchResult(
                    content_type="faq",
                    title=faq.question,
                    snippet=snippet,
                    relevance_score=relevance
                ))
        
        # Sort by relevance score
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results
    
    def _extract_snippet(self, text: str, query: str, max_length: int = 150) -> str:
        """Extract a snippet around the query match."""
        text_lower = text.lower()
        query_index = text_lower.find(query)
        
        if query_index == -1:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # Calculate snippet boundaries
        start = max(0, query_index - max_length // 2)
        end = min(len(text), start + max_length)
        
        snippet = text[start:end]
        
        # Add ellipsis if needed
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
            
        return snippet
    
    def _calculate_relevance(self, text: str, query: str) -> float:
        """Calculate relevance score for search results."""
        text_lower = text.lower()
        query_lower = query.lower()
        
        # Count occurrences
        occurrences = text_lower.count(query_lower)
        
        # Calculate score based on occurrences and text length
        if occurrences == 0:
            return 0.0
            
        # Higher score for more occurrences, normalized by text length
        score = (occurrences * len(query_lower)) / len(text_lower)
        return min(score * 100, 100.0)  # Cap at 100
    
    @classmethod
    def get_default_content(cls) -> 'HelpContent':
        """Get default help content."""
        default_faqs = [
            FAQItem(
                id="faq_001",
                question="如何建立新的排程任務？",
                answer="點擊主介面的「新增任務」按鈕，填寫任務名稱、選擇目標應用程式、設定執行時間和操作類型，然後點擊「儲存」即可。",
                category="基本操作",
                order=1
            ),
            FAQItem(
                id="faq_002",
                question="支援哪些類型的Windows操作？",
                answer="系統支援啟動應用程式、關閉應用程式、調整視窗大小、移動視窗位置、最小化/最大化視窗、點擊元素、輸入文字、發送快捷鍵等操作。",
                category="功能說明",
                order=2
            ),
            FAQItem(
                id="faq_003",
                question="如何設定條件觸發？",
                answer="在建立或編輯任務時，啟用「條件觸發」選項，然後選擇條件類型（如視窗標題包含特定文字、程序正在運行等）並設定相應的條件值。",
                category="進階功能",
                order=3
            ),
            FAQItem(
                id="faq_004",
                question="任務執行失敗時會怎麼處理？",
                answer="系統會自動重試失敗的任務，預設最多重試3次。所有執行結果都會記錄在日誌中，您可以在「排程記錄」頁面查看詳細的錯誤訊息。",
                category="故障排除",
                order=4
            ),
            FAQItem(
                id="faq_005",
                question="如何匯出執行日誌？",
                answer="在「排程記錄」頁面，您可以使用搜尋和篩選功能找到需要的日誌，然後點擊「匯出」按鈕選擇匯出格式（CSV、JSON或TXT）。",
                category="日誌管理",
                order=5
            )
        ]
        
        default_contact = ContactInfo(
            email="support@windows-scheduler.com",
            support_hours="週一至週五 9:00-18:00",
            response_time="24小時內回覆",
            website="https://windows-scheduler.com"
        )
        
        about_text = """
Windows排程控制GUI是一個功能強大的Windows應用程式自動化工具，基於Python和Tkinter開發。

主要功能：
• 排程管理：建立、編輯和管理Windows應用程式的自動化任務
• 多種觸發方式：支援時間觸發和條件觸發
• 豐富的操作類型：啟動、關閉、調整視窗、點擊、輸入文字等
• 執行監控：即時監控任務執行狀態和結果
• 日誌管理：完整的執行歷史記錄和搜尋功能
• 系統整合：與Windows-MCP深度整合，提供穩定的系統控制能力

技術特點：
• 使用Python 3.13+和現代化的uv包管理器
• 基於Tkinter的直觀圖形介面
• 多執行緒排程引擎確保穩定性
• JSON格式的資料存儲，支援備份和還原
• 完整的錯誤處理和重試機制

適用場景：
• 定時啟動和關閉應用程式
• 自動化重複性的視窗操作
• 系統維護任務的排程執行
• 基於條件的智慧觸發操作
        """
        
        return cls(
            about_text=about_text.strip(),
            faq_items=default_faqs,
            contact_info=default_contact,
            version="1.0.0",
            last_updated=datetime.now()
        )