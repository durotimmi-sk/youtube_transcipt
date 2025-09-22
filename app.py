from flask import Flask, request, jsonify
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled
)
import youtube_transcript_api # Import the module itself
import os

app = Flask(__name__)

# Add these diagnostic prints right after imports
print(f"DEBUG: youtube_transcript_api module path: {youtube_transcript_api.__file__}")
print(f"DEBUG: dir(youtube_transcript_api): {dir(youtube_transcript_api)}")
print(f"DEBUG: Type of YouTubeTranscriptApi: {type(YouTubeTranscriptApi)}") # Keep this one, it was working fine before
print(f"DEBUG: dir(YouTubeTranscriptApi): {dir(YouTubeTranscriptApi)}") # Keep this one too


@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get("video_id")
    lang = request.args.get("lang", "en") 

    if not video_id:
        return jsonify({"error": "Missing video_id parameter"}), 400

    try:
        # 1. Try exact requested language
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
        text = " ".join([entry['text'] for entry in transcript])
        return jsonify({
            "video_id": video_id,
            "language_used": lang,
            "transcript": text
        })

    except NoTranscriptFound:
        try:
            # 2. Try to fallback to another transcript
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            chosen_transcript = None

            if lang.startswith("en"):
                # Prefer English variants
                for t in transcript_list:
                    if t.language_code.startswith("en"):
                        chosen_transcript = t
                        break

            # If still none, pick the first available transcript
            if chosen_transcript is None and transcript_list:
                chosen_transcript = transcript_list[0]

            if chosen_transcript:
                transcript = chosen_transcript.fetch()
                text = " ".join([entry['text'] for entry in transcript])
                return jsonify({
                    "video_id": video_id,
                    "language_used": chosen_transcript.language_code,
                    "transcript": text
                })
            else:
                return jsonify({
                    "error": "No transcripts available for this video.",
                    "video_id": video_id
                }), 404

        except TranscriptsDisabled:
            return jsonify({
                "error": "Transcripts are disabled for this video.",
                "video_id": video_id
            }), 403
        except Exception as e:
            return jsonify({
                "error": "Transcript not available. Video might be unavailable, private, or blocked.",
                "details": str(e),
                "video_id": video_id
            }), 404

    except TranscriptsDisabled:
        return jsonify({
            "error": "Transcripts are disabled for this video.",
            "video_id": video_id
        }), 403

    except Exception as e:
        return jsonify({
            "error": "Transcript not available. Video might be unavailable, private, or blocked.",
            "details": str(e),
            "video_id": video_id
        }), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Render uses $PORT
    app.run(host="0.0.0.0", port=port)
