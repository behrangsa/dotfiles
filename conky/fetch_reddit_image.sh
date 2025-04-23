#!/bin/bash

# Directory to store the downloaded images
IMAGES_DIR="$HOME/.cache/conky/reddit_images"
CURRENT_IMAGE="$IMAGES_DIR/current_image"
LOG_FILE="$IMAGES_DIR/fetch.log"

# Create directory if it doesn't exist
mkdir -p "$IMAGES_DIR"

# Function to log messages
log_message() {
    echo "[$(date)] $1" >> "$LOG_FILE"
    # Also print to stderr for debugging
    echo "[$(date)] $1" >&2
}

# Function to get Reddit access token
get_access_token() {
    if [ -z "$REDDIT_API_KEY" ] || [ -z "$REDDIT_API_SECRET" ]; then
        log_message "Error: Reddit API credentials not found in environment"
        exit 1
    fi

    local credentials=$(echo -n "$REDDIT_API_KEY:$REDDIT_API_SECRET" | base64)
    
    response=$(curl -s -X POST \
        -H "Authorization: Basic $credentials" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=client_credentials" \
        "https://www.reddit.com/api/v1/access_token")
    
    # Debug: Log the response
    log_message "Auth Response: $response"
    
    # Validate JSON response
    if ! echo "$response" | jq . >/dev/null 2>&1; then
        log_message "Error: Invalid JSON response from auth endpoint"
        return 1
    fi
    
    local token=$(echo "$response" | jq -r '.access_token')
    if [ "$token" = "null" ] || [ -z "$token" ]; then
        log_message "Error: No access token in response"
        return 1
    fi
    
    echo "$token"
}

# Get a random image URL from the subreddit
get_random_image() {
    local access_token=$1
    local response=$(curl -s \
        -H "Authorization: Bearer $access_token" \
        -H "User-Agent: linux:conky-reddit-fetcher:v1.0" \
        "https://oauth.reddit.com/r/NewYorkNineMild/hot.json?limit=100")
    
    # Debug: Log the response
    log_message "Reddit API Response: $response"
    
    # Validate JSON response
    if ! echo "$response" | jq . >/dev/null 2>&1; then
        log_message "Error: Invalid JSON response from Reddit API"
        return 1
    fi
    
    # Extract image URLs (including galleries)
    local image_url=$(echo "$response" | jq -r '.data.children[] | 
        select(.data.post_hint == "image" or .data.is_gallery == true) |
        if .data.is_gallery then
            .data.gallery_data.items[0].media_id
        else
            .data.url
        end' | shuf -n 1)
    
    if [ -z "$image_url" ]; then
        log_message "Error: No valid image URLs found"
        return 1
    fi
    
    echo "$image_url"
}

# Download the image
download_image() {
    local url=$1
    local output="$IMAGES_DIR/$(date +%s).jpg"
    
    # Handle gallery URLs
    if [[ $url =~ ^[a-zA-Z0-9]+$ ]]; then
        url="https://i.redd.it/${url}.jpg"
    fi
    
    log_message "Attempting to download: $url"
    
    if curl -s -f -o "$output" "$url"; then
        # Only update current_image if download was successful
        ln -sf "$output" "$CURRENT_IMAGE"
        log_message "Successfully downloaded new image: $url"
        
        # Clean up old images (keep last 5)
        find "$IMAGES_DIR" -type f -name "*.jpg" -not -newer "$output" | 
            sort -r | tail -n +6 | xargs -r rm
    else
        log_message "Failed to download image: $url"
        return 1
    fi
}

# Main execution
token=$(get_access_token)
if [ -n "$token" ]; then
    image_url=$(get_random_image "$token")
    if [ -n "$image_url" ]; then
        download_image "$image_url"
    else
        log_message "Failed to get image URL"
        exit 1
    fi
else
    log_message "Failed to get access token"
    exit 1
fi