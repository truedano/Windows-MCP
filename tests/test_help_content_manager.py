"""
Tests for help content management functionality.
"""

import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.core.help_content_manager import HelpContentManager
from src.models.help_models import HelpContent, FAQItem, ContactInfo, SearchResult
from src.storage.help_content_storage import HelpContentStorage


class TestHelpContentManager(unittest.TestCase):
    """Test cases for HelpContentManager."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test storage
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock storage
        self.mock_storage = MagicMock(spec=HelpContentStorage)
        
        # Create test help content
        self.test_contact_info = ContactInfo(
            email="test@example.com",
            support_hours="9-17",
            response_time="24h",
            website="https://test.com"
        )
        
        self.test_faq_items = [
            FAQItem(
                id="faq_001",
                question="How to create a task?",
                answer="Click the create button and fill the form.",
                category="Basic",
                order=1
            ),
            FAQItem(
                id="faq_002",
                question="How to delete a task?",
                answer="Select the task and click delete.",
                category="Basic",
                order=2
            ),
            FAQItem(
                id="faq_003",
                question="How to troubleshoot errors?",
                answer="Check the logs for error details.",
                category="Troubleshooting",
                order=1
            )
        ]
        
        self.test_help_content = HelpContent(
            about_text="This is a test application for managing Windows tasks.",
            faq_items=self.test_faq_items,
            contact_info=self.test_contact_info,
            version="1.0",
            last_updated=datetime.now()
        )
        
        # Configure mock storage
        self.mock_storage.load_help_content.return_value = self.test_help_content
        self.mock_storage.save_help_content.return_value = True
        
        # Create manager with mock storage
        self.manager = HelpContentManager(self.mock_storage)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test manager initialization."""
        self.assertIsNotNone(self.manager)
        self.assertEqual(self.manager.storage, self.mock_storage)
        self.mock_storage.load_help_content.assert_called_once()
    
    def test_load_help_content(self):
        """Test loading help content."""
        content = self.manager.load_help_content()
        
        self.assertIsInstance(content, HelpContent)
        self.assertEqual(content.about_text, self.test_help_content.about_text)
        self.assertEqual(len(content.faq_items), 3)
        self.assertEqual(content.version, "1.0")
    
    def test_get_about_content(self):
        """Test getting about content."""
        about_text = self.manager.get_about_content()
        
        self.assertEqual(about_text, self.test_help_content.about_text)
    
    def test_get_faq_items(self):
        """Test getting FAQ items."""
        # Get all FAQ items
        all_items = self.manager.get_faq_items()
        self.assertEqual(len(all_items), 3)
        
        # Get FAQ items by category
        basic_items = self.manager.get_faq_items(category="Basic")
        self.assertEqual(len(basic_items), 2)
        
        troubleshooting_items = self.manager.get_faq_items(category="Troubleshooting")
        self.assertEqual(len(troubleshooting_items), 1)
        
        # Check ordering
        self.assertEqual(basic_items[0].order, 1)
        self.assertEqual(basic_items[1].order, 2)
    
    def test_get_faq_categories(self):
        """Test getting FAQ categories."""
        categories = self.manager.get_faq_categories()
        
        self.assertIn("Basic", categories)
        self.assertIn("Troubleshooting", categories)
        self.assertEqual(len(categories), 2)
    
    def test_get_faq_item_by_id(self):
        """Test getting FAQ item by ID."""
        # Existing item
        item = self.manager.get_faq_item_by_id("faq_001")
        self.assertIsNotNone(item)
        self.assertEqual(item.question, "How to create a task?")
        
        # Non-existing item
        item = self.manager.get_faq_item_by_id("faq_999")
        self.assertIsNone(item)
    
    def test_search_content(self):
        """Test content search functionality."""
        # Search in about text
        results = self.manager.search_content("application")
        self.assertTrue(len(results) > 0)
        
        # Search in FAQ questions
        results = self.manager.search_content("create")
        self.assertTrue(len(results) > 0)
        self.assertTrue(any(r.content_type == "faq" for r in results))
        
        # Search in FAQ answers
        results = self.manager.search_content("button")
        self.assertTrue(len(results) > 0)
        
        # Search with no results
        results = self.manager.search_content("nonexistent")
        self.assertEqual(len(results), 0)
        
        # Empty search
        results = self.manager.search_content("")
        self.assertEqual(len(results), 0)
    
    def test_search_relevance_scoring(self):
        """Test search relevance scoring."""
        results = self.manager.search_content("task")
        
        # Results should be sorted by relevance
        if len(results) > 1:
            for i in range(len(results) - 1):
                self.assertGreaterEqual(results[i].relevance_score, results[i + 1].relevance_score)
        
        # Check that all results have valid scores
        for result in results:
            self.assertGreaterEqual(result.relevance_score, 0.0)
            self.assertLessEqual(result.relevance_score, 1.0)
    
    def test_get_contact_info(self):
        """Test getting contact information."""
        contact_info = self.manager.get_contact_info()
        
        self.assertEqual(contact_info.email, "test@example.com")
        self.assertEqual(contact_info.support_hours, "9-17")
        self.assertEqual(contact_info.response_time, "24h")
        self.assertEqual(contact_info.website, "https://test.com")
    
    def test_update_content(self):
        """Test updating help content."""
        # Create new content
        new_content = HelpContent(
            about_text="Updated about text",
            faq_items=self.test_faq_items,
            contact_info=self.test_contact_info,
            version="2.0",
            last_updated=datetime.now()
        )
        
        # Update content
        success = self.manager.update_content(new_content)
        
        self.assertTrue(success)
        self.mock_storage.save_help_content.assert_called()
        
        # Verify content was updated
        self.assertEqual(self.manager.get_about_content(), "Updated about text")
    
    def test_add_faq_item(self):
        """Test adding new FAQ item."""
        success = self.manager.add_faq_item(
            question="How to export logs?",
            answer="Go to logs page and click export.",
            category="Advanced"
        )
        
        self.assertTrue(success)
        self.mock_storage.save_help_content.assert_called()
        
        # Check that item was added
        all_items = self.manager.get_faq_items()
        self.assertEqual(len(all_items), 4)
        
        # Check new category
        categories = self.manager.get_faq_categories()
        self.assertIn("Advanced", categories)
    
    def test_update_faq_item(self):
        """Test updating existing FAQ item."""
        success = self.manager.update_faq_item(
            faq_id="faq_001",
            question="How to create a new task?",
            answer="Updated answer for creating tasks."
        )
        
        self.assertTrue(success)
        self.mock_storage.save_help_content.assert_called()
        
        # Verify update
        item = self.manager.get_faq_item_by_id("faq_001")
        self.assertEqual(item.question, "How to create a new task?")
        self.assertEqual(item.answer, "Updated answer for creating tasks.")
    
    def test_update_nonexistent_faq_item(self):
        """Test updating non-existent FAQ item."""
        success = self.manager.update_faq_item(
            faq_id="faq_999",
            question="Non-existent item"
        )
        
        self.assertFalse(success)
    
    def test_delete_faq_item(self):
        """Test deleting FAQ item."""
        success = self.manager.delete_faq_item("faq_002")
        
        self.assertTrue(success)
        self.mock_storage.save_help_content.assert_called()
        
        # Verify deletion
        all_items = self.manager.get_faq_items()
        self.assertEqual(len(all_items), 2)
        
        item = self.manager.get_faq_item_by_id("faq_002")
        self.assertIsNone(item)
    
    def test_delete_nonexistent_faq_item(self):
        """Test deleting non-existent FAQ item."""
        success = self.manager.delete_faq_item("faq_999")
        
        self.assertFalse(success)
    
    def test_get_content_version(self):
        """Test getting content version."""
        version = self.manager.get_content_version()
        self.assertEqual(version, "1.0")
    
    def test_get_last_updated(self):
        """Test getting last updated timestamp."""
        last_updated = self.manager.get_last_updated()
        self.assertIsInstance(last_updated, datetime)
    
    def test_error_handling_load_failure(self):
        """Test error handling when loading fails."""
        # Configure mock to raise exception
        self.mock_storage.load_help_content.side_effect = Exception("Load failed")
        
        # Create new manager
        manager = HelpContentManager(self.mock_storage)
        
        # Should fall back to default content
        content = manager.load_help_content()
        self.assertIsNotNone(content)
        self.assertIn("Windows 排程控制 GUI", content.about_text)
    
    def test_error_handling_save_failure(self):
        """Test error handling when saving fails."""
        # Configure mock to fail save
        self.mock_storage.save_help_content.return_value = False
        
        success = self.manager.update_content(self.test_help_content)
        self.assertFalse(success)
    
    def test_snippet_extraction(self):
        """Test snippet extraction for search results."""
        # Test with query that appears in content
        results = self.manager.search_content("application")
        
        if results:
            result = results[0]
            self.assertIsInstance(result.snippet, str)
            self.assertLessEqual(len(result.snippet), 200)  # Should be reasonably short
    
    def test_faq_id_generation(self):
        """Test FAQ ID generation."""
        # Add multiple items to test ID generation
        existing_ids = ["faq_001", "faq_002", "faq_003"]
        new_id = self.manager._generate_faq_id(existing_ids)
        
        self.assertEqual(new_id, "faq_004")
        self.assertNotIn(new_id, existing_ids)
    
    def test_default_content_structure(self):
        """Test default content structure."""
        default_content = self.manager._get_default_content()
        
        self.assertIsInstance(default_content, HelpContent)
        self.assertIsInstance(default_content.about_text, str)
        self.assertIsInstance(default_content.faq_items, list)
        self.assertIsInstance(default_content.contact_info, ContactInfo)
        self.assertIsInstance(default_content.version, str)
        self.assertIsInstance(default_content.last_updated, datetime)
        
        # Check that default content has reasonable FAQ items
        self.assertGreater(len(default_content.faq_items), 0)
        
        # Check FAQ item structure
        for item in default_content.faq_items:
            self.assertIsInstance(item, FAQItem)
            self.assertIsInstance(item.id, str)
            self.assertIsInstance(item.question, str)
            self.assertIsInstance(item.answer, str)
            self.assertIsInstance(item.category, str)
            self.assertIsInstance(item.order, int)


class TestHelpContentManagerIntegration(unittest.TestCase):
    """Integration tests for HelpContentManager."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create real storage with temp directory
        from src.storage.help_content_storage import HelpContentStorage
        self.storage = HelpContentStorage(
            content_file=str(Path(self.temp_dir) / "help_content.json")
        )
        
        self.manager = HelpContentManager(self.storage)
    
    def tearDown(self):
        """Clean up integration test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_lifecycle(self):
        """Test full lifecycle of help content management."""
        # Initial load should create default content
        content = self.manager.load_help_content()
        self.assertIsNotNone(content)
        
        # Add a new FAQ item
        success = self.manager.add_faq_item(
            question="Integration test question?",
            answer="Integration test answer.",
            category="Testing"
        )
        self.assertTrue(success)
        
        # Search for the new item
        results = self.manager.search_content("Integration test")
        self.assertTrue(len(results) > 0)
        
        # Update the item
        faq_items = self.manager.get_faq_items(category="Testing")
        if faq_items:
            item_id = faq_items[0].id
            success = self.manager.update_faq_item(
                faq_id=item_id,
                answer="Updated integration test answer."
            )
            self.assertTrue(success)
            
            # Verify update
            updated_item = self.manager.get_faq_item_by_id(item_id)
            self.assertEqual(updated_item.answer, "Updated integration test answer.")
        
        # Create new manager instance to test persistence
        new_manager = HelpContentManager(self.storage)
        new_content = new_manager.load_help_content()
        
        # Verify content persisted
        testing_items = new_manager.get_faq_items(category="Testing")
        self.assertTrue(len(testing_items) > 0)


if __name__ == "__main__":
    unittest.main()