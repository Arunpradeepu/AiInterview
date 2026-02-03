import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import Feedback from './Feedback';

export default function RecordingApp() {
  const [isRecording, setIsRecording] = useState(false);
  const [timeLeft, setTimeLeft] = useState(120); // 2 minutes in seconds
  const [hasStarted, setHasStarted] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcriptResult, setTranscriptResult] = useState(null);
  const [error, setError] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackData, setFeedbackData] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerIntervalRef = useRef(null);
  
  const questions = [
    "Introduce yourself",
    // "What are your strengths?",
    // "What are your weaknesses?",
    // "Why should we hire you?",
    // "Tell me about a challenge you faced",
    // "Where do you see yourself in 5 years?",
    "Explain a project you worked on",
    "explain any movie ",
    // "How do you handle pressure?"
    // "sing a song",
    // "whats your plan in the weekends"
  ];
  
  const API_URL = 'https://aiinterview-production.up.railway.app';

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, []);

  // Handle timer countdown
  useEffect(() => {
    if (isRecording && timeLeft > 0) {
      timerIntervalRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            stopRecording();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, [isRecording]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getRandomQuestion = () => {
    const randomIndex = Math.floor(Math.random() * questions.length);
    setCurrentQuestion(questions[randomIndex]);
  };

  const startRecording = async () => {
    try {
      setError(null);
      setTranscriptResult(null);
      setShowFeedback(false);
      setFeedbackData(null);
      
      // Get a random question if not already set
      if (!currentQuestion) {
        getRandomQuestion();
      }
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });

      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Collect audio data
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await uploadAudio(audioBlob);
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      // Start recording
      mediaRecorder.start();
      setIsRecording(true);
      setHasStarted(true);
      setTimeLeft(120); // Reset to 2 minutes
      
      console.log('🎤 Recording started');
      
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Failed to access microphone. Please grant permission.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
      
      console.log('⏹️ Recording stopped');
    }
  };

  const uploadAudio = async (audioBlob) => {
    setIsProcessing(true);
    
    try {
      // Create form data
      const formData = new FormData();
      const audioFile = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
      formData.append('audio', audioFile);
      formData.append('question', currentQuestion);

      console.log('📤 Uploading audio...');

      // Upload to backend
      const response = await fetch(`${API_URL}/upload-recording`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        console.log('✅ Upload successful:', data);
        setTranscriptResult(data);
        
        // Automatically analyze the response
        await analyzeFeedback(data.transcript_text, data.question, data.timestamp);
      } else {
        console.error('❌ Upload failed:', data.error);
        setError(data.error || 'Failed to upload audio');
      }
      
    } catch (err) {
      console.error('❌ Error uploading audio:', err);
      setError('Failed to upload and transcribe audio');
    } finally {
      setIsProcessing(false);
    }
  };

  const analyzeFeedback = async (transcript, question, timestamp) => {
    setIsAnalyzing(true);
    
    try {
      console.log('🔄 Analyzing response...');
      
      const response = await fetch(`${API_URL}/analyze-response`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transcript: transcript,
          question: question,
          timestamp: timestamp
        })
      });

      const data = await response.json();

      if (response.ok) {
        console.log('✅ Analysis complete:', data);
        setFeedbackData(data.feedback);
        setShowFeedback(true);
      } else {
        console.error('❌ Analysis failed:', data.error);
        setError(data.error || 'Failed to analyze response');
      }
      
    } catch (err) {
      console.error('❌ Error analyzing:', err);
      setError('Failed to analyze response');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const resetRecording = () => {
    setHasStarted(false);
    setTimeLeft(120);
    setTranscriptResult(null);
    setError(null);
    setShowFeedback(false);
    setFeedbackData(null);
    setCurrentQuestion('');
    audioChunksRef.current = [];
  };

  return (
    <div className="recording-app">
      <div className="recording-container">
        <h1 className="app-title">AI Interview Practice</h1>
        
        {/* Question Selection */}
        {!hasStarted && (
          <div className="question-selector">
            <button onClick={getRandomQuestion} className="random-btn">
              Get Random Question
            </button>
            {currentQuestion && (
              <div className="selected-question">
                <strong>Selected Question:</strong>
                <p>{currentQuestion}</p>
              </div>
            )}
          </div>
        )}

        {/* Question Display During Recording */}
        {hasStarted && !showFeedback && (
          <div className="question-box">
            <h2 className="question-label">Question:</h2>
            <p className="question-text">{currentQuestion}</p>
          </div>
        )}

        {/* Timer Display */}
        {hasStarted && !showFeedback && (
          <div className={`timer-display ${timeLeft <= 10 ? 'timer-warning' : ''}`}>
            <div className="timer-circle">
              <span className="timer-text">{formatTime(timeLeft)}</span>
            </div>
            {isRecording && (
              <div className="recording-indicator">
                <span className="recording-dot"></span>
                <span>Recording...</span>
              </div>
            )}
          </div>
        )}

        {/* Start/Stop Button */}
        {!hasStarted && !showFeedback ? (
          <button 
            className="start-btn"
            onClick={startRecording}
            disabled={!currentQuestion}
          >
            {currentQuestion ? 'Start Recording' : 'Select a Question First'}
          </button>
        ) : !showFeedback && (
          <div className="button-group">
            {isRecording && (
              <button 
                className="stop-btn"
                onClick={stopRecording}
              >
                Stop Recording
              </button>
            )}
          </div>
        )}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="processing-indicator">
            <div className="spinner"></div>
            <p>Processing and transcribing your audio...</p>
          </div>
        )}

        {/* Analyzing Indicator */}
        {isAnalyzing && (
          <div className="processing-indicator">
            <div className="spinner"></div>
            <p>Analyzing your response with AI...</p>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="error-box">
            <p>❌ {error}</p>
          </div>
        )}

        {/* Feedback Component */}
        {showFeedback && feedbackData && (
          <Feedback 
            feedbackData={feedbackData}
            question={currentQuestion}
            transcript={transcriptResult?.transcript_text}
            onTryAgain={resetRecording}
          />
        )}

        {/* Instructions */}
        {!hasStarted && !showFeedback && (
          <div className="instructions">
            <h3>Instructions:</h3>
            <ul>
              <li>Click "Get Random Question" to receive an interview question</li>
              <li>Click "Start Recording" to begin your response</li>
              <li>You'll have 2 minutes to answer the question</li>
              <li>Recording will automatically stop after 2 minutes</li>
              <li>Or click "Stop Recording" to finish early</li>
              <li>Your response will be analyzed and you'll receive feedback</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}