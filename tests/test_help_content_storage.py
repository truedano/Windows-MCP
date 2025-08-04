"""
Tests for help content storage functionality.
"""

import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from src.storage.help_content_storage import HelpContentStorage
from src.models.help_models import HelpContent, FAQItem, ContactInfo, SearchResult


class TestHelpContentStorage(unittest.TestCase):
    """Test cases for HelpContentStorage class."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.storage = HelpContentStorage(
            data_dir=str(self.data_dir),
            content_file="test_help_content.json"
        )
        
        # Create test data
        self.test_faq_items = [
            FAQItem(
                id="test_001",
                question="How to create a task?",
                answer="Click the create button and fill in the details.",
                category="Basic",
                order=1
            ),
            FAQItem(
                id="test_002",
                question="How to delete a task?",
                answer="Select the task and click delete button.",
                category="Basic",
                order=2
            ),
            FAQItem(
                id="test_003",
                question="How to configure advanced settings?",
                answer="Go to settings page and modify advanced options.",
                category="Advanced",
                order=1
            )
        ]
        
        self.test_contact_info = ContactInfo(
            email="test@example.com",
            support_hours="9 AM - 5 PM",
            response_time="24 hours",
            website="https://example.com"
        )
        
        self.test_help_content = HelpContent(
            about_text="This is a test application for managing tasks.",
            faq_items=self.test_faq_items,
            contact_info=self.test_contact_info,
            version="1.0.0",
            last_updated=datetime.now()
        )
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_directory_creation(self):
        """Test that directories are created properly."""
        self.assertTrue(self.data_dir.exists())
        self.assertTrue((self.data_dir / "help_assets").exists())
    
    def test_default_content_creation(self):
        """Test creation of default help content."""
        # Storage should create default content on initialization
        content = self.storage.load_help_content()
        
        self.assertIsInstance(content, HelpContent)
        self.assertIsNotNone(content.about_text)
        self.assertGreater(len(content.faq_items), 0)
        self.assertIsInstance(content.contact_info, ContactInfo)
        self.assertIsNotNone(content.version)
        self.assertIsInstance(content.last_updated, datetime)
    
    def test_save_and_load_help_content(self):
        """Test saving and loading help content."""
        # Save test content
        success = self.storage.save_help_content(self.test_help_content)
        self.assertTrue(success)
        
        # Load content
        loaded_content = self.storage.load_help_content()
        
        # Verify content
        self.assertEqual(loaded_content.about_text, self.test_help_content.about_text)
        self.assertEqual(len(loaded_content.faq_items), len(self.test_help_content.faq_items))
        self.assertEqual(loaded_content.contact_info.email, self.test_help_content.contact_info.email)
        self.assertEqual(loaded_content.version, self.test_help_content.version)
    
    def test_content_caching(self):
        """Test content caching mechanism."""
        # Save content
        self.storage.save_help_content(self.test_help_content)
        
        # Load content twice
        content1 = self.storage.load_help_content()
        content2 = self.storage.load_help_content()
        
        # Should be the same object (cached)
        self.assertIs(content1, content2)
        
        # Clear cache and load again
        self.storage.clear_cache()
        content3 = self.storage.load_help_content()
        
        # Should be different object but same content
        self.assertIsNot(content1, content3)
        self.assertEqual(content1.about_text, content3.about_text)
    
    def test_faq_operations(self):
        """Test FAQ item operations."""
        # Save initial content
        self.storage.save_help_content(self.test_help_content)
        
        # Test load FAQ items
        faq_items = self.storage.load_faq_items()
        self.assertEqual(len(faq_items), 3)
        
        # Test add FAQ item
        new_faq = FAQItem(
            id="test_004",
            question="New question?",
            answer="New answer.",
            category="New",
            order=1
        )
        
        success = self.storage.add_faq_item(new_faq)
        self.assertTrue(success)
        
        # Verify addition
        faq_items = self.storage.load_faq_items()
        self.assertEqual(len(faq_items), 4)
        self.assertTrue(any(item.id == "test_004" for item in faq_items))
        
        # Test update FAQ item
        new_faq.answer = "Updated answer."
        success = self.storage.update_faq_item(new_faq)
        self.assertTrue(success)
        
        # Verify update
        faq_items = self.storage.load_faq_items()
        updated_item = next(item for item in faq_items if item.id == "test_004")
        self.assertEqual(updated_item.answer, "Updated answer.")
        
        # Test delete FAQ item
        success = self.storage.delete_faq_item("test_004")
        self.assertTrue(success)
        
        # Verify deletion
        faq_items = self.storage.load_faq_items()
        self.assertEqual(len(faq_items), 3)
        self.assertFalse(any(item.id == "test_004" for item in faq_items))
    
    def test_faq_duplicate_id(self):
        """Test handling of duplicate FAQ IDs."""
        # Save initial content
        self.storage.save_help_content(self.test_help_content)
        
        # Try to add FAQ with existing ID
        duplicate_faq = FAQItem(
            id="test_001",  # Duplicate ID
            question="Duplicate question?",
            answer="Duplicate answer.",
            category="Duplicate",
            order=1
        )
        
        success = self.storage.add_faq_item(duplicate_faq)
        self.assertFalse(success)
        
        # Verify no change
        faq_items = self.storage.load_faq_items()
        self.assertEqual(len(faq_items), 3)
    
    def test_contact_info_operations(self):
        """Test contact information operations."""
        # Save initial content
        self.storage.save_help_content(self.test_help_content)
        
        # Test load contact info
        contact_info = self.storage.load_contact_info()
        self.assertEqual(contact_info.email, "test@example.com")
        
        # Test save contact info
        new_contact = ContactInfo(
            email="new@example.com",
            support_hours="24/7",
            response_time="1 hour",
            website="https://new.example.com"
        )
        
        success = self.storage.save_contact_info(new_contact)
        self.assertTrue(success)
        
        # Verify update
        loaded_contact = self.storage.load_contact_info()
        self.assertEqual(loaded_contact.email, "new@example.com")
        self.assertEqual(loaded_contact.support_hours, "24/7")
    
    def test_faq_categories(self):
        """Test FAQ category operations."""
        # Save initial content
        self.storage.save_help_content(self.test_help_content)
        
        # Test get categories
        categories = self.storage.get_faq_categories()
        self.assertEqual(set(categories), {"Basic", "Advanced"})
        
        # Test get FAQ by category
        basic_faqs = self.storage.get_faq_by_category("Basic")
        self.assertEqual(len(basic_faqs), 2)
        
        advanced_faqs = self.storage.get_faq_by_category("Advanced")
        self.assertEqual(len(advanced_faqs), 1)
        
        # Verify ordering
        self.assertEqual(basic_faqs[0].order, 1)
        self.assertEqual(basic_faqs[1].order, 2)
    
    def test_search_functionality(self):
        """Test help content search."""
        # Save initial content
        self.storage.save_help_content(self.test_help_content)
        
        # Test search in FAQ questions
        results = self.storage.search_content("create")
        self.assertGreater(len(results), 0)
        
        # Find the FAQ result
        faq_results = [r for r in results if r.content_type == "faq"]
        self.assertGreater(len(faq_results), 0)
        
        # Test search in about text
        results = self.storage.search_content("application")
        about_results = [r for r in results if r.content_type == "about"]
        self.assertGreater(len(about_results), 0)
        
        # Test search in contact info
        results = self.storage.search_content("example.com")
        contact_results = [r for r in results if r.content_type == "contact"]
        self.assertGreater(len(contact_results), 0)
        
        # Test empty search
        results = self.storage.search_content("")
        self.assertEqual(len(results), 0)
        
        # Test no matches
        results = self.storage.search_content("nonexistent")
        self.assertEqual(len(results), 0)
    
    def test_search_relevance_scoring(self):
        """Test search relevance scoring."""
        # Save initial content
        self.storage.save_help_content(self.test_help_content)
        
        # Search for a term that appears in multiple places
        results = self.storage.search_content("task")
        
        # Results should be sorted by relevance (highest first)
        if len(results) > 1:
            for i in range(len(results) - 1):
                self.assertGreaterEqual(results[i].relevance_score, results[i + 1].relevance_score)
        
        # All relevance scores should be between 0 and 1
        for result in results:
            self.assertGreaterEqual(result.relevance_score, 0.0)
            self.assertLessEqual(result.relevance_score, 1.0)
    
    def test_export_and_import(self):
        """Test help content export and import."""
        # Save initial content
        self.storage.save_help_content(self.test_help_content)
        
        # Export content
        export_path = Path(self.temp_dir) / "exported_help.json"
        success = self.storage.export_help_content(export_path)
        self.assertTrue(success)
        self.assertTrue(export_path.exists())
        
        # Verify export file structure
        with open(export_path, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        self.assertIn("metadata", export_data)
        self.assertIn("help_content", export_data)
        self.assertIn("exported_at", export_data["metadata"])
        
        # Modify content
        modified_content = HelpContent(
            about_text="Modified about text",
            faq_items=[],
            contact_info=self.test_contact_info,
            version="2.0.0",
            last_updated=datetime.now()
        )
        self.storage.save_help_content(modified_content)
        
        # Import original content
        success = self.storage.import_help_content(export_path)
        self.assertTrue(success)
        
        # Verify import
        loaded_content = self.storage.load_help_content()
        self.assertEqual(loaded_content.about_text, self.test_help_content.about_text)
        self.assertEqual(len(loaded_content.faq_items), 3)
    
    def test_content_statistics(self):
        """Test content statistics generation."""
        # Save initial content
        self.storage.save_help_content(self.test_help_content)
        
        # Get statistics
        stats = self.storage.get_content_statistics()
        
        # Verify statistics
        self.assertEqual(stats["total_faq_items"], 3)
        self.assertEqual(stats["faq_categories"], 2)
        self.assertGreater(stats["about_word_count"], 0)
        self.assertGreater(stats["faq_word_count"], 0)
        self.assertGreater(stats["total_word_count"], 0)
        self.assertIn("last_updated", stats)
        self.assertEqual(stats["version"], "1.0.0")
        self.assertEqual(set(stats["categories"]), {"Advanced", "Basic"})
    
    def test_backup_and_restore(self):
        """Test backup and restore functionality."""
        # Save initial content
        self.storage.save_help_content(self.test_help_content)
        
        # Modify content to create a scenario where backup is needed
        modified_content = HelpContent(
            about_text="Modified content",
            faq_items=[],
            contact_info=self.test_contact_info,
            version="2.0.0",
            last_updated=datetime.now()
        )
        
        # Save should create backup
        success = self.storage.save_help_content(modified_content)
        self.assertTrue(success)
        
        # Verify content was saved
        loaded_content = self.storage.load_help_content()
        self.assertEqual(loaded_content.about_text, "Modified content")
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON files."""
        # Create invalid JSON file
        invalid_json_path = self.data_dir / "test_help_content.json"
        with open(invalid_json_path, 'w') as f:
            f.write("{ invalid json content")
        
        # Should return default content
        content = self.storage.load_help_content()
        self.assertIsInstance(content, HelpContent)
        
        # Should be default content (not empty)
        self.assertGreater(len(content.faq_items), 0)
    
    def test_missing_file_handling(self):
        """Test handling of missing content file."""
        # Create storage with non-existent file
        missing_storage = HelpContentStorage(
            data_dir=str(Path(self.temp_dir) / "missing"),
            content_file="missing.json"
        )
        
        # Should create default content
        content = missing_storage.load_help_content()
        self.assertIsInstance(content, HelpContent)
        self.assertGreater(len(content.faq_items), 0)
    
    def test_concurrent_access(self):
        """Test thread-safe concurrent access."""
        import threading
        import time
        
        results = []
        errors = []
        
        def save_content(content_id):
            try:
                test_content = HelpContent(
                    about_text=f"Test content {content_id}",
                    faq_items=[FAQItem(
                        id=f"faq_{content_id}",
                        question=f"Question {content_id}?",
                        answer=f"Answer {content_id}.",
                        category="Test",
                        order=content_id
                    )],
                    contact_info=self.test_contact_info,
                    version=f"1.{content_id}.0",
                    last_updated=datetime.now()
                )
                
                success = self.storage.save_help_content(test_content)
                results.append(success)
                time.sleep(0.001)  # Small delay to encourage race conditions
                
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_content, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        self.assertEqual(len(errors), 0)
        
        # Verify all saves were successful
        self.assertEqual(len(results), 5)
        self.assertTrue(all(results))
        
        # Verify final content is valid
        final_content = self.storage.load_help_content()
        self.assertIsInstance(final_content, HelpContent)
    
    def test_persistence_across_instances(self):
        """Test that content persists across storage instances."""
        # Save content with first instance
        self.storage.save_help_content(self.test_help_content)
        
        # Create new storage instance
        new_storage = HelpContentStorage(
            data_dir=str(self.data_dir),
            content_file="test_help_content.json"
        )
        
        # Verify content is loaded
        loaded_content = new_storage.load_help_content()
        self.assertEqual(loaded_content.about_text, self.test_help_content.about_text)
        self.assertEqual(len(loaded_content.faq_items), 3)
        
        # Verify search works
        results = new_storage.search_content("create")
        self.assertGreater(len(results), 0)


if __name__ == "__main__":
    unittest.main()