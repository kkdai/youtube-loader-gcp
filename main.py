import os
import tempfile
import logging
from pathlib import Path
from flask import Flask, jsonify, request
from google.cloud import secretmanager
from langchain_community.document_loaders import GoogleApiClient, GoogleApiYoutubeLoader
from transcript import get_transcripts
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)


def is_running_on_gcp():
    """Check if the application is running on Google Cloud Platform."""
    # Check for GCP-specific environment variables
    gcp_env_vars = ["K_SERVICE", "GOOGLE_CLOUD_PROJECT", "K_REVISION"]
    return any(var in os.environ for var in gcp_env_vars)


def get_secret(secret_id):
    """Get secret either from GCP Secret Manager or local environment variables."""
    logging.debug(f"Fetching secret for: {secret_id}")

    # If running on GCP, use Secret Manager
    if is_running_on_gcp():
        logging.debug("Running on GCP, using Secret Manager")
        client = secretmanager.SecretManagerServiceClient()
        name = (
            f"projects/{os.environ['PROJECT_ID']}/secrets/{secret_id}/versions/latest"
        )
        response = client.access_secret_version(request={"name": name})
        secret_data = response.payload.data.decode("UTF-8")
        logging.debug(
            f"Secret fetched successfully from Secret Manager for: {secret_id}"
        )
    else:
        # If running locally, use environment variables
        logging.debug("Running locally, using environment variables")
        env_var_name = f"GOOGLE_SECRET_KEY_{secret_id.upper()}"
        secret_data = os.environ.get(env_var_name)
        if not secret_data:
            logging.error(f"Secret not found in environment variable: {env_var_name}")
            raise ValueError(
                f"Secret not found: {secret_id}. Set the environment variable {env_var_name}"
            )
        logging.debug(f"Secret fetched successfully from environment for: {secret_id}")

    return secret_data


def init_google_api_client():
    logging.debug("Initializing GoogleApiClient")
    creds_content = get_secret("youtube_api_credentials")

    # Create a temporary file to store the credentials
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_creds_file:
        logging.debug("Writing credentials to temporary file")
        temp_creds_file.write(creds_content.encode("utf-8"))
        temp_creds_file.flush()
        temp_creds_file_path = temp_creds_file.name

    logging.debug(f"Temporary credentials file created at: {temp_creds_file_path}")

    # Convert the file path to a Path object
    temp_creds_file_path = Path(temp_creds_file_path)

    # Initialize GoogleApiClient with the path to the temporary credentials file
    google_api_client = GoogleApiClient(service_account_path=temp_creds_file_path)

    # Clean up the temporary file after use
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

        # Use Youtube Ids
        youtube_loader_ids = GoogleApiYoutubeLoader(
            google_api_client=google_api_client,
            video_ids=[v_id],
            add_video_info=True,
        )

        # Load data
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

        # Get languages from request parameters or use default
        languages_param = request.args.get("languages", "en")
        languages = languages_param.split(",")

        logging.debug(
            f"Loading YouTube transcript for video ID: {v_id} with languages: {languages}"
        )

        # Call the get_transcripts function from transcript.py
        transcript_text = get_transcripts(v_id, languages)

        logging.debug("Transcript loaded successfully")
        return jsonify({"transcript": transcript_text})
    except Exception as e:
        logging.error(
            f"An error occurred while loading transcript: {str(e)}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def hello():
    return "Hello, World!"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
