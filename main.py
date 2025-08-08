import os
import tempfile
import logging
from pathlib import Path
from flask import Flask, jsonify, request
from google.cloud import secretmanager
from langchain_community.document_loaders import GoogleApiClient, GoogleApiYoutubeLoader
from transcript import get_transcripts
import json
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)


def is_running_on_gcp():
    """Check if the application is running on Google Cloud Platform."""
    gcp_env_vars = ["K_SERVICE", "GOOGLE_CLOUD_PROJECT", "K_REVISION"]
    return any(var in os.environ for var in gcp_env_vars)


def get_secret(secret_id):
    """Get secret either from GCP Secret Manager or local environment variables."""
    logging.debug(f"Fetching secret for: {secret_id}")
    if is_running_on_gcp():
        logging.debug("Running on GCP, using Secret Manager")
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{os.environ['PROJECT_ID']}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        secret_data = response.payload.data.decode("UTF-8")
        logging.debug(f"Secret fetched successfully from Secret Manager for: {secret_id}")
    else:
        logging.debug("Running locally, using environment variables")
        env_var_name = secret_id.upper() # Simplified for local dev
        secret_data = os.environ.get(env_var_name)
        if not secret_data:
            logging.error(f"Secret not found in environment variable: {env_var_name}")
            raise ValueError(f"Secret not found: {secret_id}. Set the environment variable {env_var_name}")
        logging.debug(f"Secret fetched successfully from environment for: {secret_id}")
    return secret_data


def summarize_video_with_gemini(video_id, api_key):
    """Calls the Gemini API to summarize a YouTube video."""
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    gemini_api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }
    
    payload = {
        "contents": [{
            "parts": [
                {"text": "請用三句中文總結這部影片的內容"},
                {"file_data": {"file_uri": video_url, "mime_type": "video/youtube"}}
            ]
        }]
    }
    
    logging.debug(f"Calling Gemini API for video: {video_url}")
    response = requests.post(gemini_api_url, headers=headers, json=payload)
    response.raise_for_status()  # Will raise an exception for HTTP error codes
    
    try:
        data = response.json()
        summary = data["candidates"][0]["content"]["parts"][0]["text"]
        return summary
    except (KeyError, IndexError) as e:
        logging.error(f"Error parsing Gemini response: {e}")
        logging.error(f"Full response: {response.text}")
        raise ValueError("Could not extract summary from Gemini API response.")


@app.route("/summarize-youtube", methods=["GET"])
def summarize_youtube():
    try:
        v_id = request.args.get("v_id")
        if not v_id:
            return jsonify({"error": "Missing 'v_id' parameter"}), 400

        logging.debug(f"Summarizing YouTube video ID: {v_id}")
        api_key = get_secret("GEMINI_API_KEY")
        
        summary = summarize_video_with_gemini(v_id, api_key)
        
        logging.debug("Summary generated successfully")
        return jsonify({"summary": summary})
    except Exception as e:
        logging.error(f"An error occurred while summarizing: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def init_google_api_client():
    logging.debug("Initializing GoogleApiClient")
    creds_content = get_secret("youtube_api_credentials")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_creds_file:
        logging.debug("Writing credentials to temporary file")
        temp_creds_file.write(creds_content.encode("utf-8"))
        temp_creds_file.flush()
        temp_creds_file_path = temp_creds_file.name
    logging.debug(f"Temporary credentials file created at: {temp_creds_file_path}")
    temp_creds_file_path = Path(temp_creds_file_path)
    google_api_client = GoogleApiClient(service_account_path=temp_creds_file_path)
    os.unlink(temp_creds_file_path)
    logging.debug("Temporary credentials file deleted")
    return google_api_client


@app.route("/load-youtube-data", methods=["GET"])
def load_youtube_data():
    try:
        v_id = request.args.get("v_id")
        if not v_id:
            return jsonify({"error": "Missing 'v_id' parameter"}), 400
        logging.debug(f"Loading YouTube data for video ID: {v_id}")
        google_api_client = init_google_api_client()
        youtube_loader_ids = GoogleApiYoutubeLoader(
            google_api_client=google_api_client,
            video_ids=[v_id],
            add_video_info=True,
        )
        logging.debug("Loading data from video ID")
        ids_data = youtube_loader_ids.load()
        logging.debug("Data loaded successfully")
        return jsonify({"ids_data": str(ids_data)})
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/load-youtube-transcript", methods=["GET"])
def load_youtube_transcript():
    try:
        v_id = request.args.get("v_id")
        if not v_id:
            return jsonify({"error": "Missing 'v_id' parameter"}), 400
        languages_param = request.args.get("languages")
        if languages_param:
            languages = languages_param.split(",")
        else:
            languages = ['en', 'ja', 'zh-TW', 'zh-CN', 'zh-Hant', 'zh-Hans']
        logging.debug(f"Loading YouTube transcript for video ID: {v_id} with languages: {languages}")
        transcript_text = get_transcripts(v_id, languages)
        logging.debug("Transcript loaded successfully")
        return jsonify({"transcript": transcript_text})
    except Exception as e:
        logging.error(f"An error occurred while loading transcript: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def hello():
    return "Hello, World!"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))