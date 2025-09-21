from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled, NoStreamsFound

app = Flask(__name__)

@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get("video_id")
    lang = request.args.get("lang", "en") 
    
    if not video_id:
        return jsonify({"error": "Missing video_id parameter"}), 400

    try:
        
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
        text = " ".join([entry['text'] for entry in transcript])
        return jsonify({"video_id": video_id, "transcript": text, "language_used": lang})
    except NoTranscriptFound:
        try:
            
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            chosen_transcript = None
            
            
            if lang.startswith('en'):
                for t in transcript_list:
                    if t.language_code.startswith('en'):
                        chosen_transcript = t
                        break
            
            
            if chosen_transcript is None and transcript_list:
                chosen_transcript = transcript_list[0]
            
            if chosen_transcript:
                transcript = chosen_transcript.fetch()
                text = " ".join([entry['text'] for entry in transcript])
                return jsonify({"video_id": video_id, "transcript": text, "language_used": chosen_transcript.language_code})
            else:
                return jsonify({"error": f"No transcripts available for video_id: {video_id}"}), 404
        except TranscriptsDisabled:
            return jsonify({"error": f"Transcripts are disabled for video_id: {video_id}"}), 403
        except NoStreamsFound:
            return jsonify({"error": f"No streams found for video_id: {video_id}. It might be unavailable or private."}), 404
        except Exception as e:
            return jsonify({"error": f"An unexpected error occurred during fallback: {str(e)}"}), 500
    except TranscriptsDisabled:
        return jsonify({"error": f"Transcripts are disabled for video_id: {video_id}"}), 403
    except NoStreamsFound:
        return jsonify({"error": f"No streams found for video_id: {video_id}. It might be unavailable or private."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
