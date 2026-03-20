# Soundgasm Audio Story Finder

A simple web application to discover and listen to Soundgasm audio stories through web scraping.

## Features

- 🔍 **Search** - Search for audio stories by title and description
- 🔥 **Trending** - Browse popular stories from top creators
- 🎧 **Audio Player** - Built-in audio player for direct playback
- 📱 **Responsive** - Works on desktop and mobile devices
- ⚡ **Fast** - Efficient scraping with rate limiting

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and go to:
```
http://localhost:5000
```

## Usage

### Web Interface
- Open the app in your browser
- Browse trending stories or search for specific content
- Click "Play" to listen directly in the browser
- Click "Open" to view the story on Soundgasm

### Python API
```python
from soundgasm_scraper import SoundgasmScraper

scraper = SoundgasmScraper()

# Get trending stories
stories = scraper.get_trending_stories()

# Search for stories
results = scraper.search_stories("sleep", max_results=10)

# Get stories from specific user
user_stories = scraper.get_user_stories("Qarnivore")
```

## API Endpoints

- `GET /` - Main web interface
- `GET /api/trending` - Get trending stories
- `GET /api/search?q=query` - Search stories
- `GET /api/user/username` - Get stories from user
- `GET /api/story?url=url` - Get story details

## File Structure

```
soundgasm-app/
├── app.py              # Flask web application
├── soundgasm_scraper.py # Core scraping logic
├── requirements.txt     # Python dependencies
├── templates/
│   └── index.html      # Web interface
└── README_SOUNDGASM.md # This file
```

## How It Works

1. **Web Scraping**: Uses BeautifulSoup to parse Soundgasm pages
2. **Audio Extraction**: Finds M4A audio URLs embedded in JavaScript
3. **Rate Limiting**: Includes delays to be respectful to the server
4. **Search**: Searches through popular users' content (Soundgasm lacks built-in search)
5. **Caching**: Avoids re-scraping the same content repeatedly

## Popular Users Included

The app searches through these popular Soundgasm creators:
- Qarnivore
- Desdesbabypie
- garden_slumber
- Mangosonabeach
- sassmastah77
- rubber_foal
- fieldsoflupine
- sexuallyspecific
- SarasSerenityndSleep
- Lavendearie
- miss_honey_bun
- John17999

## Notes

- Soundgasm doesn't provide an official API, so this app scrapes public content
- Rate limiting is built-in to avoid overwhelming the servers
- Some stories may not have audio files available
- Search functionality is limited to available user content

## Troubleshooting

- If stories don't load, check your internet connection
- Some content may be geo-restricted
- Audio playback requires browser support for M4A format

## Legal

This tool is for educational purposes only. Respect content creators' rights and terms of service.
