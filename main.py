import os
from typing import Optional
from dotenv import load_dotenv
from dubbing_utils import download_dubbed_file, wait_for_dubbing_completion
from elevenlabs.client import ElevenLabs
from flask import Flask, request, jsonify, render_template

# Load environment variables
load_dotenv()

# Retrieve the API key
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError(
        "ELEVENLABS_API_KEY environment variable not found. "
        "Please set the API key in your environment variables."
    )

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

app = Flask(__name__)

def create_dub_from_url(
    source_url: str,
    source_language: str,
    target_language: str,
) -> Optional[str]:
    """
    Downloads a video from a URL, and creates a dubbed version in the target language.

    Args:
        source_url (str): The URL of the source video to dub. Can be a YouTube link, TikTok, X (Twitter) or a Vimeo link.
        source_language (str): The language of the source video.
        target_language (str): The target language to dub into.

    Returns:
        Optional[str]: The file path of the dubbed file or None if operation failed.
    """
    try:
        response = client.dubbing.dub_a_video_or_an_audio_file(
            source_url=source_url,
            target_lang=target_language,
            mode="automatic",
            source_lang=source_language,
            num_speakers=1,
            watermark=True,  # reduces the characters used
        )
    except Exception as e:
        print(f"Error during dubbing request: {e}")
        return None

    dubbing_id = response.dubbing_id
    print(f"Dubbing ID: {dubbing_id}")  # Debugging line

    if wait_for_dubbing_completion(dubbing_id):
        try:
            output_file_path = download_dubbed_file(dubbing_id, target_language)
            return output_file_path
        except Exception as e:
            print(f"Error during file download: {e}")
            return None
    else:
        print("Dubbing did not complete successfully.")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dub', methods=['POST'])
def dub():
    data = request.json
    source_url = data.get('source_url')
    source_language = data.get('source_language')
    target_language = data.get('target_language')

    if not source_url or not source_language or not target_language:
        return jsonify({'error': 'Missing required parameters'}), 400

    result = create_dub_from_url(source_url, source_language, target_language)
    if result:
        return jsonify({'message': 'Dubbing was successful!', 'file_path': result})
    else:
        return jsonify({'error': 'Dubbing failed or timed out.'}), 500

if __name__ == "__main__":
    app.run(debug=True, port=8081)
