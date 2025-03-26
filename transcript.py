import os
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig


def get_transcripts(video_id, languages):
    # Get proxy credentials from environment variables
    proxy_username = os.environ.get("PROXY_USERNAME")
    proxy_password = os.environ.get("PROXY_PASSWORD")

    # Define WebShare proxy details
    proxy_host = "proxy.webshare.io"  # WebShare proxy endpoint
    proxy_port = "80"  # Default WebShare port (adjust if needed)

    # Format proxy URL with authentication
    proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"

    # Initialize YouTubeTranscriptApi with GenericProxyConfig
    ytt_api = YouTubeTranscriptApi(
        proxy_config=GenericProxyConfig(
            http_url=proxy_url,
            https_url=proxy_url,  # Use the same URL for HTTPS (WebShare supports tunneling)
        )
    )

    # Fetch transcript
    transcript_list = ytt_api.get_transcript(video_id, languages=languages)
    transcript_texts = [snippet["text"] for snippet in transcript_list]
    return " ".join(transcript_texts)


# Example usage
if __name__ == "__main__":
    video_id = "ViA4-YWx8Y4"
    languages = ["en"]  # Specify desired languages
    try:
        transcript = get_transcripts(video_id, languages)
        print(transcript)
    except Exception as e:
        print(f"Error: {e}")
