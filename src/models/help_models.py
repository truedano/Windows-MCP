"""
Data models for help and support content.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class FAQItem:
    """FAQ item for help content."""

    id: str
    question: str
    answer: str
    category: str
    order: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "category": self.category,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FAQItem":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            question=data["question"],
            answer=data["answer"],
            category=data["category"],
            order=data["order"],
        )


@dataclass
class ContactInfo:
    """Contact information for support."""

    email: str
    support_hours: str
    response_time: str
    website: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "email": self.email,
            "support_hours": self.support_hours,
            "response_time": self.response_time,
            "website": self.website,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContactInfo":
        """Create from dictionary."""
        return cls(
            email=data["email"],
            support_hours=data["support_hours"],
            response_time=data["response_time"],
            website=data["website"],
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
        """Convert to dictionary."""
        return {
            "about_text": self.about_text,
            "faq_items": [item.to_dict() for item in self.faq_items],
            "contact_info": self.contact_info.to_dict(),
            "version": self.version,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HelpContent":
        """Create from dictionary."""
        return cls(
            about_text=data["about_text"],
            faq_items=[FAQItem.from_dict(item) for item in data["faq_items"]],
            contact_info=ContactInfo.from_dict(data["contact_info"]),
            version=data["version"],
            last_updated=datetime.fromisoformat(data["last_updated"]),
        )


@dataclass
class SearchResult:
    """Search result for help content."""

    content_type: str  # "about", "faq", "contact"
    title: str
    snippet: str
    relevance_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content_type": self.content_type,
            "title": self.title,
            "snippet": self.snippet,
            "relevance_score": self.relevance_score,
        }
