#!/usr/bin/env python3
"""
Soundgasm Audio Story Scraper
A simple app to find and play Soundgasm audio stories
"""

import requests
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
from typing import List, Dict, Optional

class SoundgasmScraper:
    def __init__(self):
        self.base_url = "https://soundgasm.net"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_stories(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        Search for audio stories on Soundgasm
        Note: Soundgasm doesn't have a built-in search, so we'll search popular users
        """
        results = []
        
        # Popular users to search through
        popular_users = [
            "Qarnivore",
            "Desdesbabypie", 
            "garden_slumber",
            "Mangosonabeach",
            "sassmastah77",
            "rubber_foal",
            "fieldsoflupine",
            "sexuallyspecific",
            "SarasSerenityndSleep",
            "Lavendearie",
            "miss_honey_bun",
            "John17999"
        ]
        
        for username in popular_users[:5]:  # Limit to first 5 for demo
            try:
                user_stories = self.get_user_stories(username)
                for story in user_stories:
                    if query.lower() in story['title'].lower() or query.lower() in story['description'].lower():
                        results.append(story)
                        if len(results) >= max_results:
                            return results
            except Exception as e:
                print(f"Error searching user {username}: {e}")
                continue
        
        return results
    
    def get_user_stories(self, username: str) -> List[Dict]:
        """Get all stories from a specific user"""
        user_url = f"{self.base_url}/u/{username}"
        
        try:
            response = self.session.get(user_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            stories = []
            
            # Find all sound details divs
            for sound_div in soup.find_all('div', class_='sound-details'):
                link = sound_div.find('a')
                if link and link.get('href'):
                    story_url = urljoin(self.base_url, link.get('href'))
                    
                    # Get title from link text
                    title = link.get_text().strip()
                    
                    # Get description
                    desc_span = sound_div.find('span', class_='soundDescription')
                    description = desc_span.get_text().strip() if desc_span else "No description available"
                    
                    # Get play count
                    play_span = sound_div.find('span', class_='playCount')
                    play_count = play_span.get_text().strip() if play_span else "0"
                    
                    # Extract username and story name from URL
                    url_match = re.match(r'.*/u/([^/]+)/([^/]+)', story_url)
                    username_extracted = url_match.group(1) if url_match else username
                    story_name = url_match.group(2) if url_match else "unknown"
                    
                    stories.append({
                        'title': title,
                        'description': description,
                        'url': story_url,
                        'audio_url': None,  # Will be fetched when needed
                        'username': username_extracted,
                        'story_name': story_name,
                        'play_count': play_count
                    })
                    
                    time.sleep(0.3)  # Be respectful
            
            return stories
            
        except Exception as e:
            print(f"Error getting stories for {username}: {e}")
            return []
    
    def get_story_details(self, story_url: str) -> Optional[Dict]:
        """Get details of a specific story"""
        try:
            response = self.session.get(story_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Unknown Title"
            
            # Extract description
            description_elem = soup.find('div', class_='description') or soup.find('p')
            description = description_elem.get_text().strip() if description_elem else "No description available"
            
            # Extract audio URL from script tags
            audio_url = None
            for script in soup.find_all('script'):
                if script.string:
                    match = re.search(r'(https://soundgasm\.net/sounds/.+\.m4a)', script.string)
                    if match:
                        audio_url = match.group(1)
                        break
            
            # Extract username and story name from URL
            url_match = re.match(r'.*/u/([^/]+)/([^/]+)', story_url)
            username = url_match.group(1) if url_match else "unknown"
            story_name = url_match.group(2) if url_match else "unknown"
            
            return {
                'title': title,
                'description': description,
                'url': story_url,
                'audio_url': audio_url,
                'username': username,
                'story_name': story_name
            }
            
        except Exception as e:
            print(f"Error getting story details from {story_url}: {e}")
            return None
    
    def get_trending_stories(self) -> List[Dict]:
        """Get trending/popular stories (placeholder implementation)"""
        # Since Soundgasm doesn't have a trending API, we'll get stories from popular users
        trending = []
        popular_users = ["Qarnivore", "Desdesbabypie", "garden_slumber", "Mangosonabeach", "sassmastah77"]
        
        for username in popular_users:
            try:
                user_stories = self.get_user_stories(username)
                trending.extend(user_stories[:3])  # Take first 3 from each user
                if len(trending) >= 15:
                    break
            except Exception as e:
                continue
        
        return trending

def main():
    """CLI interface for testing"""
    scraper = SoundgasmScraper()
    
    print("Soundgasm Audio Story Scraper")
    print("=" * 40)
    
    # Get trending stories
    print("\nGetting trending stories...")
    trending = scraper.get_trending_stories()
    
    for i, story in enumerate(trending[:10], 1):
        print(f"\n{i}. {story['title']}")
        print(f"   By: {story['username']}")
        print(f"   URL: {story['url']}")
        print(f"   Audio: {'Available' if story['audio_url'] else 'Not found'}")
        print(f"   Description: {story['description'][:100]}...")

if __name__ == "__main__":
    main()
