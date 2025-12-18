#!/usr/bin/env python3
"""
Remove Red Categories Script

This script removes non-existent categories (red links) from Wikipedia articles.
It processes the WantedCategories list and removes categories that don't exist.

If a category is not found in the text after checking 10 articles, it assumes
the category is included via a template and skips it.
"""

import os
import sys
import re
import logging
from typing import List, Optional, Tuple
from dotenv import load_dotenv
import mwclient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('remove_red_categories.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RedCategoryRemover:
    """Class to handle removal of non-existent categories from articles."""
    
    def __init__(self, site_url: str, username: str, password: str, 
                 max_check: int = 10, dry_run: bool = False):
        """
        Initialize the remover.
        
        Args:
            site_url: Wikipedia site URL (e.g., 'ar.wikipedia.org')
            username: Wikipedia username
            password: Wikipedia password
            max_check: Maximum articles to check before assuming template inclusion
            dry_run: If True, don't make actual edits
        """
        self.site_url = site_url
        self.username = username
        self.password = password
        self.max_check = max_check
        self.dry_run = dry_run
        self.site = None
        
    def connect(self) -> bool:
        """
        Connect to Wikipedia using mwclient.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to {self.site_url}...")
            self.site = mwclient.Site(self.site_url)
            
            if self.username and self.password:
                logger.info(f"Logging in as {self.username}...")
                self.site.login(self.username, self.password)
                logger.info("Login successful")
            else:
                logger.warning("No credentials provided, running without authentication")
                
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def get_wanted_categories(self) -> List[str]:
        """
        Get list of wanted categories from Special:WantedCategories.
        
        Returns:
            List of category names (without 'Category:' prefix)
        """
        try:
            logger.info("Fetching wanted categories...")
            wanted_cats = []
            
            # Query wanted categories using the API
            result = self.site.api('query', 
                                  list='querycachedspecial',
                                  qcslimit=500,
                                  qcspage='Wantedcategories')
            
            if 'query' in result and 'querycachedspecial' in result['query']:
                for item in result['query']['querycachedspecial']:
                    # Extract category name without namespace prefix
                    cat_title = item['title']
                    if ':' in cat_title:
                        cat_name = cat_title.split(':', 1)[1]
                    else:
                        cat_name = cat_title
                    wanted_cats.append(cat_name)
                    
            logger.info(f"Found {len(wanted_cats)} wanted categories")
            return wanted_cats
            
        except Exception as e:
            logger.error(f"Failed to fetch wanted categories: {e}")
            return []
    
    def get_category_members(self, category_name: str) -> List:
        """
        Get all members of a category.
        
        Args:
            category_name: Name of the category (without 'Category:' prefix)
            
        Returns:
            List of page objects
        """
        try:
            # Try with 'Category:' prefix
            category = self.site.categories[f'Category:{category_name}']
            members = list(category.members())
            
            # Also try with local namespace (e.g., 'تصنيف:' for Arabic)
            if not members:
                category = self.site.categories[category_name]
                members = list(category.members())
                
            return members
            
        except Exception as e:
            logger.error(f"Failed to get members of category '{category_name}': {e}")
            return []
    
    def check_category_in_text(self, text: str, category_name: str) -> bool:
        """
        Check if a category appears in the page text.
        
        Args:
            text: Page content
            category_name: Category name to search for
            
        Returns:
            True if category found in text, False otherwise
        """
        # Escape special regex characters in category name
        escaped_name = re.escape(category_name)
        
        # Pattern to match category in different formats
        # [[Category:Name]] or [[تصنيف:Name]] or other localizations
        patterns = [
            rf'\[\[Category:{escaped_name}\s*(?:\|[^\]]*)?\]\]',
            rf'\[\[category:{escaped_name}\s*(?:\|[^\]]*)?\]\]',
            rf'\[\[تصنيف:{escaped_name}\s*(?:\|[^\]]*)?\]\]',
            rf'\[\[CATEGORY:{escaped_name}\s*(?:\|[^\]]*)?\]\]',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
                
        return False
    
    def remove_category_from_text(self, text: str, category_name: str) -> str:
        """
        Remove a category from page text.
        
        Args:
            text: Original page content
            category_name: Category name to remove
            
        Returns:
            Modified text with category removed
        """
        # Escape special regex characters
        escaped_name = re.escape(category_name)
        
        # Patterns to match category in different formats
        patterns = [
            rf'\[\[Category:{escaped_name}\s*(?:\|[^\]]*)?\]\]\n?',
            rf'\[\[category:{escaped_name}\s*(?:\|[^\]]*)?\]\]\n?',
            rf'\[\[تصنيف:{escaped_name}\s*(?:\|[^\]]*)?\]\]\n?',
            rf'\[\[CATEGORY:{escaped_name}\s*(?:\|[^\]]*)?\]\]\n?',
        ]
        
        modified_text = text
        for pattern in patterns:
            modified_text = re.sub(pattern, '', modified_text, flags=re.IGNORECASE)
            
        return modified_text
    
    def process_category(self, category_name: str) -> Tuple[int, bool]:
        """
        Process a single wanted category.
        
        Args:
            category_name: Name of the category to process
            
        Returns:
            Tuple of (number of edits made, whether category was skipped)
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing category: {category_name}")
        logger.info(f"{'='*60}")
        
        # Get category members
        members = self.get_category_members(category_name)
        
        if not members:
            logger.info(f"No members found for category '{category_name}'")
            return 0, False
            
        logger.info(f"Found {len(members)} members")
        
        edits_made = 0
        not_found_count = 0
        
        for i, page in enumerate(members, 1):
            try:
                # Skip non-main namespace pages for safety (only process articles)
                if page.namespace != 0:
                    logger.debug(f"Skipping non-article page: {page.name}")
                    continue
                    
                logger.info(f"[{i}/{len(members)}] Checking: {page.name}")
                
                # Get page content
                text = page.text()
                
                # Check if category is in the text
                if self.check_category_in_text(text, category_name):
                    logger.info(f"  → Category found in text")
                    
                    # Remove the category
                    new_text = self.remove_category_from_text(text, category_name)
                    
                    if new_text != text:
                        if self.dry_run:
                            logger.info(f"  → [DRY RUN] Would remove category from: {page.name}")
                        else:
                            # Save the page
                            edit_summary = f"Removing non-existent category: [[Category:{category_name}]]"
                            page.save(new_text, summary=edit_summary, minor=True)
                            logger.info(f"  → Category removed successfully")
                            
                        edits_made += 1
                        not_found_count = 0  # Reset counter on successful find
                    else:
                        logger.warning(f"  → Text unchanged after removal attempt")
                else:
                    logger.info(f"  → Category not found in text")
                    not_found_count += 1
                    
                    # Check if we've exceeded the threshold
                    if not_found_count >= self.max_check:
                        logger.info(f"  → Category not found in {self.max_check} articles")
                        logger.info(f"  → Likely included via template, skipping this category")
                        return edits_made, True
                        
            except Exception as e:
                logger.error(f"Error processing page '{page.name}': {e}")
                continue
                
        return edits_made, False
    
    def run(self):
        """Main execution method."""
        logger.info("="*60)
        logger.info("Red Category Remover Started")
        logger.info("="*60)
        
        if self.dry_run:
            logger.info("*** DRY RUN MODE - No actual edits will be made ***")
            
        # Connect to Wikipedia
        if not self.connect():
            logger.error("Failed to connect to Wikipedia, exiting")
            return
            
        # Get wanted categories
        wanted_categories = self.get_wanted_categories()
        
        if not wanted_categories:
            logger.info("No wanted categories found")
            return
            
        # Process each category
        total_edits = 0
        skipped_categories = 0
        
        for i, category_name in enumerate(wanted_categories, 1):
            logger.info(f"\nProcessing category {i}/{len(wanted_categories)}")
            
            try:
                edits, skipped = self.process_category(category_name)
                total_edits += edits
                
                if skipped:
                    skipped_categories += 1
                    
            except Exception as e:
                logger.error(f"Error processing category '{category_name}': {e}")
                continue
                
        # Summary
        logger.info("\n" + "="*60)
        logger.info("Summary")
        logger.info("="*60)
        logger.info(f"Total categories processed: {len(wanted_categories)}")
        logger.info(f"Categories skipped (template-based): {skipped_categories}")
        logger.info(f"Total edits made: {total_edits}")
        logger.info("="*60)


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    site_url = os.getenv('WIKI_SITE', 'ar.wikipedia.org')
    username = os.getenv('WIKI_USERNAME', '')
    password = os.getenv('WIKI_PASSWORD', '')
    max_check = int(os.getenv('MAX_ARTICLES_CHECK', '10'))
    
    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv
    
    # Validate configuration
    if not username or not password:
        logger.warning("WIKI_USERNAME or WIKI_PASSWORD not set in environment")
        logger.warning("Running without authentication (limited functionality)")
        
    # Create and run remover
    remover = RedCategoryRemover(
        site_url=site_url,
        username=username,
        password=password,
        max_check=max_check,
        dry_run=dry_run
    )
    
    remover.run()


if __name__ == '__main__':
    main()
