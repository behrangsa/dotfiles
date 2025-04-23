#!/usr/bin/env python3

import os
import sys
import json
import random
import logging
from datetime import datetime
from pathlib import Path
import requests
from typing import Optional
import base64
from bs4 import BeautifulSoup
from PIL import Image
import io
import mimetypes

# Configure logging
IMAGES_DIR = Path.home() / '.cache' / 'conky' / 'reddit_images'
LOG_FILE = IMAGES_DIR / 'fetch.log'
CURRENT_IMAGE = IMAGES_DIR / 'current_image'

# Create directory if it doesn't exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stderr)
    ],
    datefmt='%c'
)
logger = logging.getLogger(__name__)

def get_access_token() -> Optional[str]:
    """Get Reddit API access token using client credentials."""
    try:
        api_key = os.environ.get('REDDIT_API_KEY')
        api_secret = os.environ.get('REDDIT_API_SECRET')
        
        if not api_key or not api_secret:
            logger.error("Reddit API credentials not found in environment")
            return None
            
        auth = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
        headers = {
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(
            'https://www.reddit.com/api/v1/access_token',
            headers=headers,
            data={'grant_type': 'client_credentials'}
        )
        response.raise_for_status()
        
        token_data = response.json()
        if 'access_token' not in token_data:
            logger.error("No access token in response")
            return None
            
        return token_data['access_token']
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting access token: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing auth response: {e}")
        return None

def get_random_image(access_token: str) -> Optional[str]:
    """Get a random image URL from the subreddit."""
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'User-Agent': 'linux:conky-reddit-fetcher:v1.0'
        }
        
        response = requests.get(
            'https://oauth.reddit.com/r/NewYorkNineMild/hot.json',
            headers=headers,
            params={'limit': 100}
        )
        response.raise_for_status()
        
        data = response.json()
        posts = data['data']['children']
        
        # Filter for image posts and gallery posts
        image_posts = []
        for post in posts:
            post_data = post['data']
            if post_data.get('post_hint') == 'image':
                image_posts.append(post_data['url'])
            elif post_data.get('is_gallery'):
                if 'gallery_data' in post_data and post_data['gallery_data']['items']:
                    media_id = post_data['gallery_data']['items'][0]['media_id']
                    image_posts.append(f"https://i.redd.it/{media_id}.jpg")
        
        if not image_posts:
            logger.error("No valid image URLs found")
            return None
            
        return random.choice(image_posts)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Reddit posts: {e}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error parsing Reddit response: {e}")
        return None

def is_valid_image(file_path: Path) -> bool:
    """Verify if a file is actually an image by checking its magic numbers."""
    # Dictionary of known image file signatures (magic numbers)
    IMAGE_SIGNATURES = {
        b'\xFF\xD8\xFF': 'jpg',  # JPEG
        b'\x89PNG\r\n\x1a\n': 'png',  # PNG
        b'GIF87a': 'gif',  # GIF
        b'GIF89a': 'gif',  # GIF
    }
    
    try:
        with open(file_path, 'rb') as f:
            # Read first 8 bytes which should cover most image signatures
            file_start = f.read(8)
            
        return any(file_start.startswith(sig) for sig in IMAGE_SIGNATURES.keys())
    except Exception as e:
        logger.error(f"Error checking image validity: {e}")
        return False

def extract_image_from_html(html_content: str) -> Optional[str]:
    """Extract the actual image URL from an HTML page."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for meta og:image first (common in preview pages)
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
            
        # Look for the first image that seems to be the main content
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Skip small icons and buttons
                if img.get('width') and int(img.get('width')) < 100:
                    continue
                if 'icon' in src.lower() or 'logo' in src.lower():
                    continue
                return src
                
        return None
    except Exception as e:
        logger.error(f"Error parsing HTML: {e}")
        return None

def resize_image(image_data: bytes, max_width: int = 640, max_height: int = 150) -> bytes:
    """Resize the image data to fit within the specified dimensions while maintaining aspect ratio."""
    try:
        # Open image from bytes
        img = Image.open(io.BytesIO(image_data))
        
        # Calculate new dimensions maintaining aspect ratio
        width_ratio = max_width / img.width
        height_ratio = max_height / img.height
        ratio = min(width_ratio, height_ratio)
        
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        
        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert back to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95)
        return output.getvalue()
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        return image_data

def verify_and_save_image(response: requests.Response, output_path: Path) -> bool:
    """Verify and save content as image, returns True if successful."""
    content_type = response.headers.get('content-type', '').lower()
    
    if 'text/html' in content_type:
        # This is an HTML page, try to extract the actual image
        image_url = extract_image_from_html(response.text)
        if not image_url:
            logger.error("Could not find image in HTML page")
            return False
            
        # Download the actual image
        logger.info(f"Found actual image URL in HTML: {image_url}")
        try:
            img_response = requests.get(image_url, stream=True)
            img_response.raise_for_status()
            if not 'image' in img_response.headers.get('content-type', '').lower():
                logger.error("Extracted URL is not an image")
                return False
            response = img_response
        except requests.RequestException as e:
            logger.error(f"Failed to download actual image: {e}")
            return False
    elif not 'image' in content_type:
        logger.error(f"Invalid content type: {content_type}")
        return False
    
    try:
        # Get image content
        image_data = response.content
        
        # Resize image
        resized_image_data = resize_image(image_data)
        
        # Save the resized image
        with output_path.open('wb') as f:
            f.write(resized_image_data)
            
        return True
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return False

def download_image(url: str) -> bool:
    """Download the image and update the current image symlink."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Generate unique filename using timestamp
        output_path = IMAGES_DIR / f"{int(datetime.now().timestamp())}.jpg"
        
        if not verify_and_save_image(response, output_path):
            return False
        
        # Update symlink
        if CURRENT_IMAGE.exists():
            CURRENT_IMAGE.unlink()
        CURRENT_IMAGE.symlink_to(output_path)
        
        logger.info(f"Successfully downloaded new image: {url}")
        
        # Clean up old images (keep last 5)
        image_files = sorted(
            [f for f in IMAGES_DIR.glob("*.jpg")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        for old_file in image_files[5:]:
            old_file.unlink()
        
        return True
        
    except requests.RequestException as e:
        logger.error(f"Failed to download image: {e}")
        return False
    except OSError as e:
        logger.error(f"Failed to save image: {e}")
        return False

def main():
    """Main execution function."""
    token = get_access_token()
    if not token:
        sys.exit(1)
        
    image_url = get_random_image(token)
    if not image_url:
        sys.exit(1)
        
    if not download_image(image_url):
        sys.exit(1)

if __name__ == "__main__":
    main()