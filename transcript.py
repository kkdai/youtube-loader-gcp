from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import os


def get_transcripts(video_id, languages):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        transcript_texts = [snippet["text"] for snippet in transcript_list]
        return " ".join(transcript_texts)
    except NoTranscriptFound:
        return f"No transcript found for video {video_id} with languages {languages}."
    except TranscriptsDisabled:
        return f"Transcripts are disabled for video {video_id}."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


# Example usage (only runs when script is executed directly)
if __name__ == "__main__":
    video_id = "YOUR_VIDEO_ID"
    languages = ["en", "de"]
    transcript_text = get_transcripts(video_id, languages)
    print(transcript_text)
