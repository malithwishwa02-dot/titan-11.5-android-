#!/usr/bin/env python3
"""
Soundgasm Audio Story Web App
A simple web interface to find and play Soundgasm audio stories
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import time
from soundgasm_scraper import SoundgasmScraper

app = Flask(__name__)
CORS(app)

# Initialize scraper
scraper = SoundgasmScraper()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/trending')
def get_trending():
    """Get trending stories"""
    try:
        stories = scraper.get_trending_stories()
        return jsonify({
            'success': True,
            'stories': stories[:20]  # Limit to 20 stories
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search')
def search_stories():
    """Search for stories"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400
    
    try:
        stories = scraper.search_stories(query, max_results=20)
        return jsonify({
            'success': True,
            'stories': stories,
            'query': query
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/<username>')
def get_user_stories(username):
    """Get stories from a specific user"""
    try:
        stories = scraper.get_user_stories(username)
        return jsonify({
            'success': True,
            'stories': stories,
            'username': username
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/audio')
def get_audio_url():
    """Get audio URL for a specific story"""
    story_url = request.args.get('url', '').strip()
    
    if not story_url:
        return jsonify({
            'success': False,
            'error': 'Story URL is required'
        }), 400
    
    try:
        story = scraper.get_story_details(story_url)
        if story and story.get('audio_url'):
            return jsonify({
                'success': True,
                'audio_url': story['audio_url']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Audio URL not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/story')
def get_story_details():
    """Get details of a specific story"""
    story_url = request.args.get('url', '').strip()
    
    if not story_url:
        return jsonify({
            'success': False,
            'error': 'Story URL is required'
        }), 400
    
    try:
        story = scraper.get_story_details(story_url)
        if story:
            return jsonify({
                'success': True,
                'story': story
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Story not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Soundgasm Audio Story App...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
