#!/usr/bin/env python3
"""
Unit tests for the Red Category Remover script.
Tests category detection, removal logic, and template detection counter.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from remove_red_categories import RedCategoryRemover


class TestCategoryDetection(unittest.TestCase):
    """Tests for category detection in text."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.remover = RedCategoryRemover(
            site_url='test.wikipedia.org',
            username='test',
            password='test',
            max_check=10,
            dry_run=True
        )
    
    def test_check_category_english_format(self):
        """Test detection of English category format."""
        text = "Some article text\n[[Category:Test Category]]"
        self.assertTrue(self.remover.check_category_in_text(text, "Test Category"))
    
    def test_check_category_arabic_format(self):
        """Test detection of Arabic category format (تصنيف)."""
        text = "Some article text\n[[تصنيف:تصنيف اختبار]]"
        self.assertTrue(self.remover.check_category_in_text(text, "تصنيف اختبار"))
    
    def test_check_category_with_sort_key(self):
        """Test detection of category with sort key."""
        text = "Some text\n[[Category:Test Category|SortKey]]"
        self.assertTrue(self.remover.check_category_in_text(text, "Test Category"))
    
    def test_check_category_case_insensitive(self):
        """Test case-insensitive detection."""
        text = "Some text\n[[category:Test Category]]"
        self.assertTrue(self.remover.check_category_in_text(text, "Test Category"))
    
    def test_check_category_not_found(self):
        """Test when category is not in text."""
        text = "Some article text without categories"
        self.assertFalse(self.remover.check_category_in_text(text, "Test Category"))
    
    def test_check_category_different_category(self):
        """Test when different category is present."""
        text = "Some text\n[[Category:Other Category]]"
        self.assertFalse(self.remover.check_category_in_text(text, "Test Category"))
    
    def test_check_category_special_chars(self):
        """Test detection with special regex characters in category name."""
        text = "Some text\n[[Category:Test (Category)]]"
        self.assertTrue(self.remover.check_category_in_text(text, "Test (Category)"))
    
    def test_check_category_with_spaces(self):
        """Test detection of category with trailing spaces."""
        text = "Some text\n[[Category:Test Category ]]"
        self.assertTrue(self.remover.check_category_in_text(text, "Test Category"))


class TestCategoryRemoval(unittest.TestCase):
    """Tests for category removal logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.remover = RedCategoryRemover(
            site_url='test.wikipedia.org',
            username='test',
            password='test',
            max_check=10,
            dry_run=True
        )
    
    def test_remove_category_english(self):
        """Test removal of English category format."""
        text = "Article text\n[[Category:Test Category]]\nMore text"
        result = self.remover.remove_category_from_text(text, "Test Category")
        self.assertNotIn("[[Category:Test Category]]", result)
        self.assertIn("Article text", result)
        self.assertIn("More text", result)
    
    def test_remove_category_arabic(self):
        """Test removal of Arabic category format."""
        text = "مقالة\n[[تصنيف:تصنيف اختبار]]\nنص إضافي"
        result = self.remover.remove_category_from_text(text, "تصنيف اختبار")
        self.assertNotIn("[[تصنيف:تصنيف اختبار]]", result)
        self.assertIn("مقالة", result)
    
    def test_remove_category_with_sort_key(self):
        """Test removal of category with sort key."""
        text = "Text\n[[Category:Test|SortKey]]\nMore"
        result = self.remover.remove_category_from_text(text, "Test")
        self.assertNotIn("[[Category:Test|SortKey]]", result)
    
    def test_remove_category_preserves_other_categories(self):
        """Test that other categories are preserved."""
        text = "Text\n[[Category:Remove Me]]\n[[Category:Keep Me]]"
        result = self.remover.remove_category_from_text(text, "Remove Me")
        self.assertNotIn("[[Category:Remove Me]]", result)
        self.assertIn("[[Category:Keep Me]]", result)
    
    def test_remove_category_special_chars(self):
        """Test removal with special regex characters."""
        text = "Text\n[[Category:Test (Category)]]\nMore"
        result = self.remover.remove_category_from_text(text, "Test (Category)")
        self.assertNotIn("[[Category:Test (Category)]]", result)
    
    def test_remove_category_no_match(self):
        """Test that text is unchanged when category not present."""
        text = "Text\n[[Category:Other Category]]"
        result = self.remover.remove_category_from_text(text, "Test Category")
        self.assertEqual(text, result)


class TestTemplateDetection(unittest.TestCase):
    """Tests for template detection (10-article rule)."""
    
    # Constants for mock data
    MOCK_TEXT_NO_CATEGORY = "No category here"
    
    def setUp(self):
        """Set up test fixtures."""
        self.remover = RedCategoryRemover(
            site_url='test.wikipedia.org',
            username='test',
            password='test',
            max_check=10,
            dry_run=True
        )
    
    def test_max_check_default(self):
        """Test default max_check value."""
        remover = RedCategoryRemover(
            site_url='test.wikipedia.org',
            username='test',
            password='test'
        )
        self.assertEqual(remover.max_check, 10)
    
    def test_max_check_custom(self):
        """Test custom max_check value."""
        remover = RedCategoryRemover(
            site_url='test.wikipedia.org',
            username='test',
            password='test',
            max_check=5
        )
        self.assertEqual(remover.max_check, 5)
    
    @patch.object(RedCategoryRemover, 'get_category_members')
    def test_skips_after_max_check_not_found(self, mock_get_members):
        """Test that category is skipped after max_check consecutive not-founds."""
        # Create mock pages that don't have the category in text
        mock_pages = []
        for i in range(12):
            page = Mock()
            page.namespace = 0
            page.name = f"Article {i}"
            page.text.return_value = self.MOCK_TEXT_NO_CATEGORY
            mock_pages.append(page)
        
        mock_get_members.return_value = iter(mock_pages)
        
        # Process the category
        edits, skipped = self.remover.process_category("Test Category")
        
        self.assertEqual(edits, 0)
        self.assertTrue(skipped)
    
    @patch.object(RedCategoryRemover, 'get_category_members')
    def test_resets_counter_on_found(self, mock_get_members):
        """Test that counter resets when category is found."""
        # Create mock pages: 5 without category, then 1 with, then 5 without
        mock_pages = []
        
        # First 5 without category
        for i in range(5):
            page = Mock()
            page.namespace = 0
            page.name = f"Article {i}"
            page.text.return_value = self.MOCK_TEXT_NO_CATEGORY
            mock_pages.append(page)
        
        # One with category
        page_with_cat = Mock()
        page_with_cat.namespace = 0
        page_with_cat.name = "Article with category"
        page_with_cat.text.return_value = "Text [[Category:Test Category]] more"
        page_with_cat.save = Mock()
        mock_pages.append(page_with_cat)
        
        # 5 more without category
        for i in range(5):
            page = Mock()
            page.namespace = 0
            page.name = f"Article {i + 6}"
            page.text.return_value = self.MOCK_TEXT_NO_CATEGORY
            mock_pages.append(page)
        
        mock_get_members.return_value = iter(mock_pages)
        
        # Process the category
        edits, skipped = self.remover.process_category("Test Category")
        
        # Should have made 1 edit (dry run counts as edit)
        self.assertEqual(edits, 1)
        # Should not be skipped yet (only 5 not found after reset)
        self.assertFalse(skipped)


class TestConnection(unittest.TestCase):
    """Tests for connection handling."""
    
    @patch('remove_red_categories.mwclient.Site')
    def test_connect_success(self, mock_site_class):
        """Test successful connection."""
        mock_site = Mock()
        mock_site_class.return_value = mock_site
        
        remover = RedCategoryRemover(
            site_url='test.wikipedia.org',
            username='testuser',
            password='testpass'
        )
        
        result = remover.connect()
        
        self.assertTrue(result)
        mock_site_class.assert_called_once_with('test.wikipedia.org')
        mock_site.login.assert_called_once_with('testuser', 'testpass')
    
    @patch('remove_red_categories.mwclient.Site')
    def test_connect_without_credentials(self, mock_site_class):
        """Test connection without credentials."""
        mock_site = Mock()
        mock_site_class.return_value = mock_site
        
        remover = RedCategoryRemover(
            site_url='test.wikipedia.org',
            username='',
            password=''
        )
        
        result = remover.connect()
        
        self.assertTrue(result)
        mock_site.login.assert_not_called()
    
    @patch('remove_red_categories.mwclient.Site')
    def test_connect_failure(self, mock_site_class):
        """Test connection failure handling."""
        mock_site_class.side_effect = Exception("Connection failed")
        
        remover = RedCategoryRemover(
            site_url='test.wikipedia.org',
            username='testuser',
            password='testpass'
        )
        
        result = remover.connect()
        
        self.assertFalse(result)


class TestDryRun(unittest.TestCase):
    """Tests for dry-run mode."""
    
    def test_dry_run_flag(self):
        """Test that dry_run flag is properly set."""
        remover = RedCategoryRemover(
            site_url='test.wikipedia.org',
            username='test',
            password='test',
            dry_run=True
        )
        self.assertTrue(remover.dry_run)
        
        remover = RedCategoryRemover(
            site_url='test.wikipedia.org',
            username='test',
            password='test',
            dry_run=False
        )
        self.assertFalse(remover.dry_run)


if __name__ == '__main__':
    unittest.main()
