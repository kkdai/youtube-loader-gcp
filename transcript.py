import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def parse_srt(srt_data):
    """Parses SRT formatted text and returns only the transcript."""
    # Remove SRT timing and numbering
    text_only = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', srt_data)
    # Remove any remaining metadata or tags
    text_only = re.sub(r'<[^>]+>', '', text_only)
    # Join lines and return
    return ' '.join(text_only.strip().split('\n'))

def get_transcripts(video_id, api_key, languages):
    """
    Fetches video transcripts using the YouTube Data API.
    """
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        captions = youtube.captions().list(part="snippet", videoId=video_id).execute()

        transcript_text = f"No transcript found for video {video_id} with languages {languages}."
        
        for caption in captions.get("items", []):
            lang_code = caption['snippet']['language']
            if lang_code in languages:
                caption_id = caption['id']
                # Download the specified caption track in srt format
                caption_data = youtube.captions().download(id=caption_id, tfmt="srt").execute()
                
                # The response is the SRT content directly
                if caption_data:
                    transcript_text = parse_srt(caption_data)
                    # Return after finding the first matching language
                    return transcript_text

        return transcript_text

    except HttpError as e:
        error_content = e.content.decode('utf-8')
        return f"An HTTP error {e.resp.status} occurred: {error_content}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# Example usage (only runs when script is executed directly)
if __name__ == "__main__":
    # This part requires setting the API_KEY environment variable for local testing
    import os
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("Please set the YOUTUBE_API_KEY environment variable.")
    else:
        video_id = "KsYicre9mjg"
        languages = ["en", "zh-TW"]
        transcript = get_transcripts(video_id, api_key, languages)
        print(transcript)