#Youtube Official Working fetcher and html displayer all in one
import os
from datetime import datetime
import logging
from googleapiclient.discovery import build
from dotenv import load_dotenv
import pandas as pd
import pytz
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Channel IDs to track
CHANNEL_IDS = [
    "UCR8bJIY-5FjZX7ZfU2RHe3w",  # Channel 1
    "UCED3hlYdD0SlCff7jJ8tF3Q",  # Channel 2
    "UCFYGr5NPq7klB5N0tb5Cdyg",  # Channel 3
    "UCSX8DZVtyvQ2Rf_lumekb3g",  # Channel 4
]

def setup_youtube_api():
    """Initialize YouTube API client"""
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY_2")
    if not api_key:
        raise ValueError("YouTube API key not found in environment variables")
    return build("youtube", "v3", developerKey=api_key)

def get_channel_stats(youtube, channel_id):
    """Fetch channel statistics"""
    try:
        request = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        )
        response = request.execute()

        if not response['items']:
            logging.error(f"No data found for channel {channel_id}")
            return None

        channel = response['items'][0]
        return {
            'Channel Name': channel['snippet']['title'],
            'Subscribers': channel['statistics']['subscriberCount'],
            'Total Videos': channel['statistics']['videoCount'],
            'Total Views': channel['statistics']['viewCount'],
            'Channel Created': channel['snippet']['publishedAt'],
            'Channel ID': channel_id,
            'Description': channel['snippet']['description'],
            'Channel URL': f"https://www.youtube.com/channel/{channel_id}"
        }
    except Exception as e:
        logging.error(f"Error fetching data for channel {channel_id}: {str(e)}")
        return None

def get_latest_videos(youtube, channel_id, max_results=1):
    """Fetch only the latest video from a channel"""
    try:
        # Get upload playlist ID
        channel_response = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()
        
        playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get only the latest video
        videos_response = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=1  # Only get 1 video
        ).execute()

        videos = []
        if videos_response['items']:  # If there's a video
            item = videos_response['items'][0]  # Get the first (most recent) video
            video_id = item['contentDetails']['videoId']
            
            # Get video statistics
            video_stats = youtube.videos().list(
                part="statistics,contentDetails",
                id=video_id
            ).execute()['items'][0]
            
            videos.append({
                'Video Title': item['snippet']['title'],
                'Video ID': video_id,
                'Upload Date': item['snippet']['publishedAt'],
                'Views': video_stats['statistics'].get('viewCount', 0),
                'Likes': video_stats['statistics'].get('likeCount', 0),
                'Comments': video_stats['statistics'].get('commentCount', 0),
                'Duration': format_duration(video_stats['contentDetails']['duration']),
                'Video URL': f"https://www.youtube.com/watch?v={video_id}",
                'Thumbnail': item['snippet']['thumbnails']['high']['url'],
                'Description': item['snippet']['description']
            })
        
        return videos
    except Exception as e:
        logging.error(f"Error fetching videos for channel {channel_id}: {str(e)}")
        return []

def format_duration(duration):
    """Convert YouTube duration format to readable format"""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return "00:00"
    
    hours, minutes, seconds = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    seconds = int(seconds) if seconds else 0
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

def get_week_label(date):
    """Get week label using fixed date ranges"""
    day = date.day
    
    if 1 <= day <= 7:
        week = 1
    elif 8 <= day <= 14:
        week = 2
    elif 15 <= day <= 21:
        week = 3
    else:  # 22 and above
        week = 4
        
    return f"{date.strftime('%B')} Week {week}"

def save_to_html(channels_data, videos_data, output_path='templates/index.html'):
    """Generate HTML report"""
    os.makedirs('templates', exist_ok=True)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create a list of all videos with their channel info for sorting
    all_videos = []
    for channel_id, videos in videos_data.items():
        channel_info = next((c for c in channels_data if c and c['Channel ID'] == channel_id), None)
        if channel_info and videos:
            video = videos[0]
            upload_date = datetime.strptime(video['Upload Date'], "%Y-%m-%dT%H:%M:%SZ")
            all_videos.append({
                'upload_date': upload_date,
                'formatted_date': upload_date.strftime("%m/%d/%Y"),
                'channel_info': channel_info,
                'video': video
            })
    
    # Sort videos by upload date (newest first)
    all_videos.sort(key=lambda x: x['upload_date'], reverse=True)
    
    # Start HTML content
    html_content = f"""
    <html>
    <head>
        <title>YouTube Channel Monitor</title>
        <style>
            body {{ 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #1a1a1a;
                color: #e1e1e1;
            }}
            h1 {{
                color: #ffffff;
                font-size: 24px;
                margin-bottom: 10px;
            }}
            p {{
                color: #888888;
                margin-bottom: 20px;
            }}
            table {{ 
                border-collapse: collapse; 
                width: 100%;
                background-color: #242424;
                border-radius: 8px;
                overflow: hidden;
            }}
            th, td {{ 
                border: 1px solid #333333;
                padding: 12px; 
                text-align: left; 
                vertical-align: middle;
            }}
            th {{ 
                background-color: #2d2d2d;
                color: #ffffff;
                font-weight: 500;
                position: sticky;
                top: 0;
            }}
            tr:hover {{
                background-color: #2a2a2a;
            }}
            img {{ 
                width: 160px; 
                height: 90px; 
                object-fit: cover;
                border-radius: 4px;
            }}
            .video-title {{
                font-weight: 500;
                color: #60a5fa;
                text-decoration: none;
            }}
            .video-title:hover {{
                color: #93c5fd;
                text-decoration: none;
            }}
            td:first-child {{  /* Upload Date column */
                color: #ffffff;
            }}
            td:nth-child(2) {{  /* Subscribers column */
                color: #f59e0b;
            }}
            td:nth-child(3) {{  /* Channel Name column */
                color: #ffffff;
            }}
            td:nth-child(4) {{  /* Views column */
                color: #10b981;
            }}
            .week-divider {{
                background-color: #2d2d2d;
                font-weight: 700;
                color: #ffffff;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                font-size: 18px;
            }}
            .week-divider td {{
                padding: 12px;
                border-top: 2px solid #333333;
                border-bottom: 2px solid #333333;
                text-align: center;
            }}
            .week-divider:hover {{
                background-color: #2d2d2d;
            }}
        </style>
    </head>
    <body>
        <h1>YouTube Channel Monitor</h1>
        <p>Last updated: {current_time}</p>
        <table>
            <tr>
                <th>Upload Date</th>
                <th>Subscribers</th>
                <th>Channel Name</th>
                <th>Views</th>
                <th>Thumbnail</th>
                <th>Video Title</th>
                <th>Duration</th>
                <th>Description</th>
            </tr>
    """
    
    # Add sorted videos to HTML with week grouping
    current_week = None
    for video_data in all_videos:
        week_label = get_week_label(video_data['upload_date'])
        
        if week_label != current_week:
            html_content += f"""
                <tr class="week-divider">
                    <td colspan="8">{week_label}</td>
                </tr>
            """
            current_week = week_label
            
        html_content += f"""
            <tr>
                <td>{video_data['formatted_date']}</td>
                <td>{int(video_data['channel_info']['Subscribers']):,}</td>
                <td>{video_data['channel_info']['Channel Name']}</td>
                <td>{int(video_data['video']['Views']):,}</td>
                <td><img src="{video_data['video']['Thumbnail']}" alt="Thumbnail"></td>
                <td><a class="video-title" href="{video_data['video']['Video URL']}">{video_data['video']['Video Title']}</a></td>
                <td>{video_data['video']['Duration']}</td>
                <td>{video_data['video']['Description'][:200]}...</td>
            </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def load_existing_videos():
    """Load existing videos from index.html if it exists"""
    try:
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract video IDs from existing content
            video_ids = re.findall(r'watch\?v=([^"]+)', content)
            return set(video_ids)
    except FileNotFoundError:
        return set()

def main():
    try:
        # Load existing videos
        existing_videos = load_existing_videos()
        
        # Initialize YouTube API
        youtube = setup_youtube_api()
        
        # Get channel statistics
        channels_data = []
        videos_data = {}
        
        for channel_id in CHANNEL_IDS:
            # Get channel stats
            channel_stats = get_channel_stats(youtube, channel_id)
            if channel_stats:
                channels_data.append(channel_stats)
            
            # Get latest videos
            videos = get_latest_videos(youtube, channel_id, max_results=5)  # Get more videos
            if videos:
                # Only keep videos that aren't already in the existing set
                new_videos = [v for v in videos if v['Video ID'] not in existing_videos]
                if new_videos:
                    videos_data[channel_id] = new_videos

        # Save to HTML (only if there are new videos)
        if videos_data:
            save_to_html(channels_data, videos_data)
            logging.info("Report updated successfully")
        else:
            logging.info("No new videos found")

    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        raise

if __name__ == "__main__":
    main()