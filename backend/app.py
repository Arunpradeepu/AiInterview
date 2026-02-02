from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import assemblyai as aai
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import requests
import json
# from dotenv import load_dotenv
# import os

app = Flask(__name__)
CORS(app)

# load_dotenv()

# print("AssemblyAI key:", os.getenv("ASSEMBLYAI_API_KEY"))
# print("OpenRouter key:", os.getenv("OPENROUTER_API_KEY"))
# Configure AssemblyAI
aai.settings.api_key = "4a09c2d229b34383a6f9a66ea7dc8338"
# aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY").strip()
OPENROUTER_API_KEY = "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"
# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY").strip()
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Configure folders
RECORDINGS_FOLDER = 'recordings'
TRANSCRIPTS_FOLDER = 'transcripts'
FEEDBACK_FOLDER = 'feedback'

os.makedirs(RECORDINGS_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPTS_FOLDER, exist_ok=True)
os.makedirs(FEEDBACK_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'ogg', 'wma', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-recording', methods=['POST'])
def upload_recording():
    """
    Receives audio recording from frontend, saves it, and transcribes it
    """
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    file = request.files['audio']
    question = request.form.get('question', 'Unknown question')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'webm'
        audio_filename = f"recording_{timestamp}.{original_ext}"
        
        # Save the audio file
        audio_path = os.path.join(RECORDINGS_FOLDER, audio_filename)
        file.save(audio_path)
        
        print(f"✅ Audio saved: {audio_path}")
        
        # Transcribe the audio using AssemblyAI
        print("🔄 Starting transcription...")
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_path)
        
        if transcript.status == aai.TranscriptStatus.completed:
            print("✅ Transcription completed")
            
            # Save transcript as TXT
            txt_filename = f"transcript_{timestamp}.txt"
            txt_path = os.path.join(TRANSCRIPTS_FOLDER, txt_filename)
            
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(transcript.text)
            
            # Also save as SRT
            srt_filename = f"transcript_{timestamp}.srt"
            srt_path = os.path.join(TRANSCRIPTS_FOLDER, srt_filename)
            
            subtitles = transcript.export_subtitles_srt()
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(subtitles)
            
            print(f"✅ Transcript saved: {txt_path}")
            print(f"✅ SRT saved: {srt_path}")
            
            # Save question with transcript for analysis
            metadata_filename = f"metadata_{timestamp}.json"
            metadata_path = os.path.join(TRANSCRIPTS_FOLDER, metadata_filename)
            
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump({
                    'question': question,
                    'timestamp': timestamp,
                    'audio_file': audio_filename,
                    'transcript_file': txt_filename
                }, f, indent=2)
            
            return jsonify({
                'success': True,
                'message': 'Recording uploaded and transcribed successfully',
                'audio_file': audio_filename,
                'transcript_file': txt_filename,
                'srt_file': srt_filename,
                'transcript_text': transcript.text,
                'audio_path': audio_path,
                'transcript_path': txt_path,
                'srt_path': srt_path,
                'timestamp': timestamp,
                'question': question
            }), 200
            
        else:
            print(f"❌ Transcription failed: {transcript.error}")
            return jsonify({
                'error': f'Transcription failed: {transcript.error}'
            }), 500
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze-response', methods=['POST'])
def analyze_response():
    """
    Analyzes the transcript using OpenRouter API (free model)
    """
    try:
        data = request.json
        question = data.get('question')
        transcript_text = data.get('transcript')
        timestamp = data.get('timestamp')
        
        if not question or not transcript_text:
            return jsonify({'error': 'Question and transcript are required'}), 400
        
        print(f"🔄 Analyzing response for question: {question}")
        
        # Create the analysis prompt
        analysis_prompt = f"""You are an expert interview coach. Analyze the following interview response and provide detailed feedback.

Interview Question: "{question}"

Candidate's Response: "{transcript_text}"

Please analyze this response and provide:
1. A score out of 10
2. What the candidate did well (strengths)
3. What the candidate did poorly (weaknesses)
4. Specific suggestions for improvement

Format your response EXACTLY as follows:

SCORE: [number]/10

STRENGTHS:
- [strength 1]
- [strength 2]
- [strength 3]

WEAKNESSES:
- [weakness 1]
- [weakness 2]
- [weakness 3]

IMPROVEMENTS:
- [improvement 1]
- [improvement 2]
- [improvement 3]

OVERALL FEEDBACK:
[2-3 sentence summary]"""

        # Call OpenRouter API with free model
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Interview Feedback App"
        }
        
        payload = {
            "model": "tngtech/tng-r1t-chimera:free",  # Free model
            "messages": [
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ]
        }
        
        print("📤 Sending request to OpenRouter API...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"❌ OpenRouter API error: {response.text}")
            return jsonify({'error': f'API error: {response.text}'}), 500
        
        result = response.json()
        feedback_text = result['choices'][0]['message']['content']
        
        print("✅ Analysis completed")
        
        # Parse the feedback
        parsed_feedback = parse_feedback(feedback_text)
        
        # Save feedback to file
        if timestamp:
            feedback_filename = f"feedback_{timestamp}.json"
            feedback_path = os.path.join(FEEDBACK_FOLDER, feedback_filename)
            
            with open(feedback_path, "w", encoding="utf-8") as f:
                json.dump({
                    'question': question,
                    'transcript': transcript_text,
                    'raw_feedback': feedback_text,
                    'parsed_feedback': parsed_feedback,
                    'timestamp': timestamp
                }, f, indent=2)
            
            print(f"✅ Feedback saved: {feedback_path}")
        
        return jsonify({
            'success': True,
            'feedback': parsed_feedback,
            'raw_feedback': feedback_text
        }), 200
        
    except Exception as e:
        print(f"❌ Error analyzing response: {str(e)}")
        return jsonify({'error': str(e)}), 500

def parse_feedback(feedback_text):
    """
    Parse the LLM feedback into structured format
    """
    try:
        lines = feedback_text.strip().split('\n')
        
        score = 0
        strengths = []
        weaknesses = []
        improvements = []
        overall = ""
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('SCORE:'):
                # Extract score
                score_text = line.replace('SCORE:', '').strip()
                try:
                    score = float(score_text.split('/')[0])
                except:
                    score = 0
            
            elif line.startswith('STRENGTHS:'):
                current_section = 'strengths'
            elif line.startswith('WEAKNESSES:'):
                current_section = 'weaknesses'
            elif line.startswith('IMPROVEMENTS:'):
                current_section = 'improvements'
            elif line.startswith('OVERALL FEEDBACK:'):
                current_section = 'overall'
            
            elif line.startswith('-') and current_section:
                point = line.lstrip('- ').strip()
                if current_section == 'strengths':
                    strengths.append(point)
                elif current_section == 'weaknesses':
                    weaknesses.append(point)
                elif current_section == 'improvements':
                    improvements.append(point)
            
            elif current_section == 'overall' and line:
                overall += line + " "
        
        return {
            'score': score,
            'strengths': strengths if strengths else ['Good attempt at answering the question'],
            'weaknesses': weaknesses if weaknesses else ['Could provide more specific examples'],
            'improvements': improvements if improvements else ['Practice articulating thoughts more clearly'],
            'overall': overall.strip() if overall else 'Keep practicing to improve your interview skills.'
        }
    
    except Exception as e:
        print(f"⚠️ Error parsing feedback: {str(e)}")
        # Return default feedback if parsing fails
        return {
            'score': 5,
            'strengths': ['You attempted to answer the question'],
            'weaknesses': ['Response could be more detailed'],
            'improvements': ['Practice providing specific examples'],
            'overall': 'Keep practicing to improve your interview responses.'
        }

@app.route('/download-audio/<filename>', methods=['GET'])
def download_audio(filename):
    """Download audio recording"""
    try:
        filepath = os.path.join(RECORDINGS_FOLDER, secure_filename(filename))
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/download-transcript/<filename>', methods=['GET'])
def download_transcript(filename):
    """Download transcript file"""
    try:
        filepath = os.path.join(TRANSCRIPTS_FOLDER, secure_filename(filename))
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/list-recordings', methods=['GET'])
def list_recordings():
    """List all recordings and transcripts"""
    try:
        recordings = []
        
        # Get all audio files
        audio_files = [f for f in os.listdir(RECORDINGS_FOLDER) if os.path.isfile(os.path.join(RECORDINGS_FOLDER, f))]
        
        for audio_file in audio_files:
            # Extract timestamp from filename
            timestamp_part = audio_file.replace('recording_', '').rsplit('.', 1)[0]
            
            # Find corresponding files
            txt_file = f"transcript_{timestamp_part}.txt"
            srt_file = f"transcript_{timestamp_part}.srt"
            feedback_file = f"feedback_{timestamp_part}.json"
            
            txt_exists = os.path.exists(os.path.join(TRANSCRIPTS_FOLDER, txt_file))
            srt_exists = os.path.exists(os.path.join(TRANSCRIPTS_FOLDER, srt_file))
            feedback_exists = os.path.exists(os.path.join(FEEDBACK_FOLDER, feedback_file))
            
            recordings.append({
                'audio_file': audio_file,
                'txt_file': txt_file if txt_exists else None,
                'srt_file': srt_file if srt_exists else None,
                'feedback_file': feedback_file if feedback_exists else None,
                'timestamp': timestamp_part
            })
        
        return jsonify({
            'recordings': recordings,
            'count': len(recordings)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'recordings_folder': RECORDINGS_FOLDER,
        'transcripts_folder': TRANSCRIPTS_FOLDER,
        'feedback_folder': FEEDBACK_FOLDER
    }), 200

if __name__ == '__main__':
    print("🚀 Starting Flask server...")
    print(f"📁 Recordings folder: {os.path.abspath(RECORDINGS_FOLDER)}")
    print(f"📄 Transcripts folder: {os.path.abspath(TRANSCRIPTS_FOLDER)}")
    print(f"📊 Feedback folder: {os.path.abspath(FEEDBACK_FOLDER)}")
    app.run(debug=True, port=5001)