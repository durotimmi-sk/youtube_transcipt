from flask import Flask, request, jsonify
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled
)
import os

app = Flask(__name__)

@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get("video_id")
    lang = request.args.get("lang", "en") 
    
    if not video_id:
        return jsonify({"error": "Missing video_id parameter"}), 400

    ytt_api = YouTubeTranscriptApi() # Instantiate the API client

    try:
        # 1. Try to get the transcript for the exact requested language using the new API
        fetched_transcript = ytt_api.fetch(video_id, languages=[lang])
        
        # The fetched_transcript object is iterable, yielding snippet dictionaries
        text = " ".join([entry['text'] for entry in fetched_transcript])
        
        return jsonify({
            "video_id": video_id,
            "language_used": fetched_transcript.language_code, # Use the actual language code from the fetched transcript
            "transcript": text
        })

    except NoTranscriptFound:
        try:
            # 2. If exact language not found, try to find a fallback using the new API
            transcript_list = ytt_api.list(video_id) # Use ytt_api.list() to get a TranscriptList object

            chosen_transcript_obj = None # This will be a Transcript object metadata

            # Prioritize English variants if an English language was requested or defaulted to
            if lang.startswith("en"):
                try:
                    # find_transcript can take a list of languages. We'll try common English variants.
                    chosen_transcript_obj = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
                except NoTranscriptFound:
                    pass # Continue to look for any other language if English variants are not found
            
            # If no specific English or requested language found, try any available transcript.
            # The TranscriptList is iterable, so we can get the first available one if any.
            if chosen_transcript_obj is None and transcript_list:
                chosen_transcript_obj = next(iter(transcript_list), None)

            if chosen_transcript_obj:
                # Fetch the actual transcript data using .fetch() on the Transcript object
                transcript_data = chosen_transcript_obj.fetch() 
                text = " ".join([entry['text'] for entry in transcript_data]) # Iterate over FetchedTranscriptSnippet objects
                
                return jsonify({
                    "video_id": video_id,
                    "language_used": chosen_transcript_obj.language_code,
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
            # Catch other exceptions like 'RequestBlocked' or 'IpBlocked' if not using proxies, or other network issues.
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
