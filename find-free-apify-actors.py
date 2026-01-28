#!/usr/bin/env python3
"""
Find free Apify actors for YouTube downloading
"""

import requests
import json

def search_apify_actors(query, token):
    """Search for Apify actors"""
    
    response = requests.get(
        'https://api.apify.com/v2/store',
        params={
            'token': token,
            'search': query,
            'limit': 20
        }
    )
    
    if response.status_code != 200:
        print(f"Failed to search actors: {response.status_code}")
        return []
    
    data = response.json()
    return data.get('data', {}).get('items', [])

def main():
    token = input("Enter your Apify API token: ").strip()
    
    if not token:
        print("Token required")
        return
    
    print("🔍 Searching for YouTube-related actors...\n")
    
    # Search terms
    searches = ['youtube', 'video downloader', 'youtube download', 'youtube scraper']
    
    all_actors = []
    
    for search_term in searches:
        print(f"Searching for: {search_term}")
        actors = search_apify_actors(search_term, token)
        all_actors.extend(actors)
        print(f"Found {len(actors)} actors")
    
    # Remove duplicates
    unique_actors = {}
    for actor in all_actors:
        actor_id = actor.get('id')
        if actor_id not in unique_actors:
            unique_actors[actor_id] = actor
    
    print(f"\n📊 Found {len(unique_actors)} unique actors")
    
    # Filter for free/cheap actors
    print("\n🆓 Free and low-cost YouTube actors:")
    print("="*60)
    
    for actor in unique_actors.values():
        name = actor.get('name', 'Unknown')
        username = actor.get('username', 'Unknown')
        title = actor.get('title', 'No title')
        pricing = actor.get('pricing', {})
        
        # Check if it's free or cheap
        monthly_free = pricing.get('monthlyFreeUsage', 0)
        price_per_run = pricing.get('pricePerRun', 0)
        
        if monthly_free > 0 or price_per_run == 0:
            print(f"Actor: {username}~{name}")
            print(f"Title: {title}")
            print(f"Monthly free usage: ${monthly_free}")
            print(f"Price per run: ${price_per_run}")
            print(f"URL: https://console.apify.com/actors/{actor.get('id')}")
            print("-" * 40)

if __name__ == "__main__":
    main()