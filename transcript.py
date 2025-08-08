from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

def get_transcripts(video_id, languages):
    """
    Fetches video transcripts using the youtube-transcript-api library.
    """
    try:
        # Fetch the transcript for the given video ID and languages
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        
        # Extract the text from each transcript snippet
        transcript_texts = [snippet["text"] for snippet in transcript_list]
        
        # Join the snippets into a single string
        return " ".join(transcript_texts)
        
    except NoTranscriptFound:
        return f"No transcript found for video {video_id} with the specified languages: {languages}."
    except TranscriptsDisabled:
        return f"Transcripts are disabled for video {video_id}."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# Example usage
if __name__ == "__main__":
    video_id = "KsYicre9mjg"  # Example video ID
    # Default languages for testing
    languages = ['en', 'ja', 'zh-TW', 'zh-CN'] 
    transcript = get_transcripts(video_id, languages)
    print(transcript)