# Plan for Removing Red Categories from Articles

## Overview
This project aims to create a Python script that automatically removes non-existent categories (red links) from Wikipedia articles. The script will process the WantedCategories list and clean up articles by removing categories that don't exist.

## Implementation Strategy

### 1. Core Components

#### 1.1 Authentication Module
- Use environment variables for secure credential storage
- Required variables:
  - `WIKI_USERNAME`: Wikipedia username
  - `WIKI_PASSWORD`: Wikipedia password
  - `WIKI_SITE`: Wikipedia site (e.g., 'ar.wikipedia.org')
- Use `mwclient` library for MediaWiki API interaction

#### 1.2 Category Processing Logic
- Fetch the WantedCategories list from the wiki
- For each wanted category:
  1. Get all members (articles) that use this category
  2. Check each article's content for the category
  3. Remove the category from the article if found in the text
  
#### 1.3 Template Detection
- **Smart Skip Logic**: If the script checks 10 articles and doesn't find the category in the text, it means the category is included via a template
- When template-based inclusion is detected, skip to the next category
- This prevents unnecessary processing and protects template-based categorization

### 2. Workflow

```
Start
  ↓
Load credentials from environment variables
  ↓
Connect to Wikipedia using mwclient
  ↓
Fetch WantedCategories list
  ↓
For each wanted category:
  ↓
  Get category members
  ↓
  Initialize counter = 0
  ↓
  For each member article:
    ↓
    Read article content
    ↓
    Search for category in text
    ↓
    Found in text?
    ├─ Yes: Remove category and save
    │        Reset counter = 0
    │        Continue to next article
    └─ No:  Increment counter
            ↓
            counter >= 10?
            ├─ Yes: Category is template-based
            │        Skip to next category
            └─ No:  Continue to next article
  ↓
  Move to next category
  ↓
End
```

### 3. Technical Details

#### 3.1 Dependencies
- `mwclient`: For MediaWiki API interaction
- `python-dotenv`: For loading environment variables from .env file
- `re`: For regex pattern matching (built-in)

#### 3.2 Key Functions

**get_wanted_categories()**
- Query the Special:WantedCategories page
- Return list of category names

**get_category_members(category_name)**
- Get all pages in a specific category
- Return list of page objects

**check_category_in_text(page_content, category_name)**
- Search for category syntax in page text
- Handle different category formats: `[[Category:Name]]`, `[[تصنيف:Name]]`
- Return True if found, False otherwise

**remove_category_from_page(page, category_name)**
- Remove category from page text
- Preserve other content and formatting
- Save the page with edit summary

**process_wanted_categories()**
- Main orchestration function
- Implements the template detection logic (10-article rule)
- Handles errors and logging

### 4. Safety Features

#### 4.1 Error Handling
- Catch and log all exceptions
- Continue processing other categories if one fails
- Implement retry logic for network issues

#### 4.2 Edit Summaries
- Clear edit summary: "Removing non-existent category: [[Category:Name]]"
- Include bot flag if running as a bot account

#### 4.3 Rate Limiting
- Respect Wikipedia's API rate limits
- Add delays between edits if necessary
- Monitor for edit conflicts

### 5. Configuration

#### 5.1 Environment Variables (.env file)
```
WIKI_USERNAME=YourUsername
WIKI_PASSWORD=YourPassword
WIKI_SITE=ar.wikipedia.org
MAX_ARTICLES_CHECK=10
```

#### 5.2 Script Parameters
- Maximum articles to check before skipping (default: 10)
- Edit summary template
- Dry-run mode for testing

### 6. Testing Strategy

#### 6.1 Unit Tests
- Test category detection in text
- Test category removal logic
- Test template detection counter

#### 6.2 Integration Tests
- Test with sandbox pages
- Verify connection to Wikipedia
- Test error handling

#### 6.3 Manual Testing
- Run in dry-run mode first
- Test with a small subset of categories
- Verify edits on Wikipedia

### 7. Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Run the script
python remove_red_categories.py

# Run in dry-run mode (no actual edits)
python remove_red_categories.py --dry-run
```

### 8. Logging

- Log all actions: category processing, edits made, categories skipped
- Log level: INFO for normal operations, DEBUG for detailed information
- Output: Both console and log file

### 9. Future Enhancements

- Support for multiple wikis
- Web interface for monitoring progress
- Statistics and reporting
- Whitelist of categories to never remove
- Batch processing optimization

## Implementation Phases

### Phase 1: Setup (Completed when this plan is done)
- [x] Create plan.md

### Phase 2: Basic Structure
- [ ] Create main Python script
- [ ] Implement authentication
- [ ] Create requirements.txt
- [ ] Create .env.example

### Phase 3: Core Functionality
- [ ] Implement wanted categories fetching
- [ ] Implement category member retrieval
- [ ] Implement category detection in text
- [ ] Implement category removal logic

### Phase 4: Smart Features
- [ ] Implement template detection (10-article rule)
- [ ] Add error handling
- [ ] Add logging

### Phase 5: Testing & Documentation
- [ ] Test with sandbox
- [ ] Update README
- [ ] Add usage examples

## Notes

- The 10-article threshold is configurable via environment variable
- The script should be run with appropriate bot permissions if making many edits
- Always test with dry-run mode first
- Keep detailed logs for audit purposes
