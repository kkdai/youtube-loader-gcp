from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
import os


def get_transcripts(video_id, languages):
    # Get proxy credentials from environment variables
    proxy_username = os.environ.get("PROXY_USERNAME")
    proxy_password = os.environ.get("PROXY_PASSWORD")

    ytt_api = YouTubeTranscriptApi(
        proxy_config=WebshareProxyConfig(
            proxy_username=proxy_username,
            proxy_password=proxy_password,
        )
    )
    transcript_list = ytt_api.fetch(video_id, languages=languages)
    transcript_texts = [snippet["text"] for snippet in transcript_list.to_raw_data()]
    return " ".join(transcript_texts)


# Example usage (only runs when script is executed directly)
if __name__ == "__main__":
    video_id = "YOUR_VIDEO_ID"
    languages = ["en", "de"]
    transcript_text = get_transcripts(video_id, languages)
    print(transcript_text)
