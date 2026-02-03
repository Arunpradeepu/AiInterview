import React from 'react';
import './Feedback.css';

export default function Feedback({ feedbackData, question, transcript, onTryAgain }) {
  const { score, strengths, weaknesses, improvements, overall } = feedbackData;

  // Determine score color
  const getScoreColor = (score) => {
    if (score >= 8) return '#27ae60'; // Green
    if (score >= 6) return '#f39c12'; // Orange
    return '#e74c3c'; // Red
  };

  // Determine score label
  const getScoreLabel = (score) => {
    if (score >= 9) return 'Excellent';
    if (score >= 8) return 'Very Good';
    if (score >= 7) return 'Good';
    if (score >= 6) return 'Average';
    if (score >= 5) return 'Below Average';
    return 'Needs Improvement';
  };

  return (
    <div className="feedback-container">
      <h2 className="feedback-title">📊 Interview Feedback</h2>

      {/* Question Asked */}
      <div className="feedback-section question-section">
        <h3>Question:</h3>
        <p className="question-display">{question}</p>
      </div>

      {/* Score Display */}
      <div className="score-section">
        <div className="score-circle" style={{ borderColor: getScoreColor(score) }}>
          <div className="score-value" style={{ color: getScoreColor(score) }}>
            {score}/10
          </div>
          <div className="score-label" style={{ color: getScoreColor(score) }}>
            {getScoreLabel(score)}
          </div>
        </div>
      </div>

      {/* Your Response */}
      <div className="feedback-section transcript-section">
        <h3>Your Response:</h3>
        <div className="transcript-box">
          <p>{transcript}</p>
        </div>
      </div>

      {/* Strengths */}
      <div className="feedback-section strengths-section">
        <h3>✅ What You Did Well:</h3>
        <ul className="feedback-list good-list">
          {strengths.map((strength, index) => (
            <li key={index}>
              <span className="bullet">✓</span>
              {strength}
            </li>
          ))}
        </ul>
      </div>

      {/* Weaknesses */}
      <div className="feedback-section weaknesses-section">
        <h3>❌ Areas That Need Work:</h3>
        <ul className="feedback-list bad-list">
          {weaknesses.map((weakness, index) => (
            <li key={index}>
              <span className="bullet">✗</span>
              {weakness}
            </li>
          ))}
        </ul>
      </div>

      {/* Improvements */}
      <div className="feedback-section improvements-section">
        <h3>💡 How to Improve:</h3>
        <ul className="feedback-list improve-list">
          {improvements.map((improvement, index) => (
            <li key={index}>
              <span className="bullet">→</span>
              {improvement}
            </li>
          ))}
        </ul>
      </div>

      {/* Overall Feedback */}
      <div className="feedback-section overall-section">
        <h3>📝 Overall Feedback:</h3>
        <p className="overall-text">{overall}</p>
      </div>

      {/* Action Buttons */}
      <div className="feedback-actions">
        <button onClick={onTryAgain} className="try-again-btn">
          Try Another Question
        </button>
      </div>
    </div>
  );
}