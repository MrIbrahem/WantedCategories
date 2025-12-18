# WantedCategories - Red Category Remover

A Python script that automatically removes non-existent categories (red links) from Wikipedia articles by processing the WantedCategories list.

## Overview

This tool helps maintain Wikipedia by cleaning up red category links from articles. It intelligently detects when categories are included via templates (rather than directly in article text) and skips them to avoid unnecessary processing.

## Features

- ✅ Connects to Wikipedia using `mwclient` library
- ✅ Fetches the WantedCategories list automatically
- ✅ Processes each category's member articles
- ✅ Removes non-existent categories from article text
- ✅ Smart template detection: skips categories after checking 10 articles without finding them in text
- ✅ Secure credential management via environment variables
- ✅ Comprehensive logging to file and console
- ✅ Dry-run mode for safe testing
- ✅ Error handling and resilience

## How It Works

1. **Fetch WantedCategories**: Retrieves the list of wanted (non-existent) categories from Special:WantedCategories
2. **Get Category Members**: For each wanted category, gets all articles that use it
3. **Check Article Text**: Examines each article's content for the category
4. **Remove Category**: If found in text, removes it from the article
5. **Template Detection**: If 10 consecutive articles don't have the category in their text, the script assumes it's included via a template and skips to the next category

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/MrIbrahem/WantedCategories.git
cd WantedCategories
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` file with your Wikipedia credentials:
```
WIKI_SITE=ar.wikipedia.org
WIKI_USERNAME=YourUsername
WIKI_PASSWORD=YourPassword
MAX_ARTICLES_CHECK=10
```

## Usage

### Basic Usage

```bash
python remove_red_categories.py
```

### Dry Run Mode (No Actual Edits)

Test the script without making any changes:

```bash
python remove_red_categories.py --dry-run
```

### Check Logs

All actions are logged to `remove_red_categories.log`:

```bash
tail -f remove_red_categories.log
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WIKI_SITE` | Wikipedia site URL | `ar.wikipedia.org` |
| `WIKI_USERNAME` | Your Wikipedia username | (required) |
| `WIKI_PASSWORD` | Your Wikipedia password | (required) |
| `MAX_ARTICLES_CHECK` | Articles to check before assuming template inclusion | `10` |

## Project Structure

```
WantedCategories/
├── plan.md                      # Detailed implementation plan
├── remove_red_categories.py     # Main script
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## Safety Features

- **Dry-run mode**: Test without making edits
- **Template detection**: Avoids breaking template-based categorization
- **Error handling**: Continues processing even if individual pages fail
- **Edit summaries**: Clear explanation of each edit
- **Logging**: Comprehensive logs for auditing
- **Main namespace only**: Only processes articles (namespace 0)

## Algorithm Details

### Template Detection Logic

The script uses a smart counter-based approach:

1. For each wanted category, iterate through its members
2. Check if the category appears in the article text
3. If found: remove it and reset counter
4. If not found: increment counter
5. If counter reaches `MAX_ARTICLES_CHECK` (default: 10): skip category

This ensures categories that are included via templates (not directly in text) are left alone.

## Example Output

```
2024-01-15 10:30:00 - INFO - Connecting to ar.wikipedia.org...
2024-01-15 10:30:01 - INFO - Login successful
2024-01-15 10:30:02 - INFO - Fetching wanted categories...
2024-01-15 10:30:03 - INFO - Found 50 wanted categories
============================================================
Processing category: Example Category
============================================================
2024-01-15 10:30:04 - INFO - Found 25 members
2024-01-15 10:30:05 - INFO - [1/25] Checking: Article Name
2024-01-15 10:30:05 - INFO -   → Category found in text
2024-01-15 10:30:06 - INFO -   → Category removed successfully
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Author

Created by MrIbrahem

## Support

If you encounter any issues or have questions, please open an issue on GitHub.