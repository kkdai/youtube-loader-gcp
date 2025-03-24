import os
import tempfile
import logging
from pathlib import Path
from flask import Flask, jsonify, request
from google.cloud import secretmanager
from langchain_community.document_loaders import GoogleApiClient, GoogleApiYoutubeLoader

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)


def get_secret(secret_id):
    logging.debug(f"Fetching secret for: {secret_id}")
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{os.environ['PROJECT_ID']}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    secret_data = response.payload.data.decode("UTF-8")
    logging.debug(f"Secret fetched successfully for: {secret_id}, {secret_data[:50]}")
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


@app.route("/", methods=["GET"])
def hello():
    return "Hello, World!"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
