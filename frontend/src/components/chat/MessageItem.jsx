import React, { useState } from 'react';
import { Shield, AlertCircle, Clock, ThumbsDown } from 'lucide-react';

const MessageItem = ({ msg, expandedResults, setExpandedResults, index, sessionId }) => {
  const isUser = msg.type === 'user';
  const [feedbackSent, setFeedbackSent] = useState(false);
  
  const handleFeedback = async () => {
    if (feedbackSent) return;
    try {
      const response = await fetch('http://localhost:8000/api/v1/history/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          feedback_type: 'wrong_result',
          comment: 'User marked this AI report/result as incorrect.'
        })
      });
      if (response.ok) {
        setFeedbackSent(true);
      }
    } catch (error) {
      console.error("Feedback error:", error);
    }
  };

  if (isUser) {
    return (
      <div style={{marginBottom: '30px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end'}}>
        <div style={{backgroundColor: '#3b82f6', padding: '12px 20px', borderRadius: '15px 15px 0 15px', maxWidth: '80%', fontSize: '14px'}}>
          {msg.text}
        </div>
      </div>
    );
  }

  const isError = msg.intent === 'ERROR';

  return (
    <div style={{marginBottom: '30px', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', width: '100%'}}>
      <div style={{
        width: '100%', 
        backgroundColor: isError ? '#450a0a' : '#1a2235', 
        padding: '25px', 
        borderRadius: '15px', 
        border: isError ? '1px solid #ef4444' : '1px solid rgba(255,255,255,0.1)'
      }}>
        <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px', color: isError ? '#f87171' : '#3b82f6', fontSize: '13px', fontWeight: 'bold'}}>
          {isError ? <AlertCircle size={16} /> : <Shield size={16} />} 
          {isError ? "시스템 오류" : "AI 분석 보고서"}
          <span style={{flex: 1}}></span>
          <span style={{fontSize: '10px', color: '#6b7280'}}>{msg.intent}</span>
        </div>
        
        <div style={{fontSize: '14px', lineHeight: '1.7', color: '#d1d5db', whiteSpace: 'pre-wrap', backgroundColor: 'rgba(255,255,255,0.03)', padding: '15px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.05)'}}>
          {msg.mode === 'flash' ? (
            <div style={{display: 'flex', flexDirection: 'column', gap: '10px'}}>
              <div style={{display: 'inline-flex', alignSelf: 'flex-start', padding: '2px 8px', backgroundColor: 'rgba(59,130,246,0.2)', color: '#60a5fa', borderRadius: '4px', fontSize: '10px', fontWeight: '800', border: '1px solid rgba(59,130,246,0.3)', marginBottom: '5px'}}>
                ⚡ 특정 시점 상황 분석
              </div>
              <div style={{fontSize: '15px', color: '#f3f4f6', fontWeight: '500'}}>{msg.report}</div>
            </div>
          ) : (
            msg.report
          )}
        </div>

        {/* Feedback Section */}
        {msg.intent !== 'CHITCHAT' && msg.intent !== 'ERROR' && (
          <div style={{marginTop: '10px', display: 'flex', justifyContent: 'flex-end'}}>
            <button 
              onClick={handleFeedback}
              disabled={feedbackSent}
              style={{
                display: 'flex', alignItems: 'center', gap: '6px', 
                background: feedbackSent ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', 
                color: feedbackSent ? '#10b981' : '#ef4444',
                border: feedbackSent ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid rgba(239, 68, 68, 0.2)',
                padding: '6px 12px', borderRadius: '6px', fontSize: '11px', cursor: feedbackSent ? 'default' : 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <ThumbsDown size={12} />
              {feedbackSent ? "오답 신고가 접수되었습니다. (학습에 반영)" : "잘못된 결과 (피드백)"}
            </button>
          </div>
        )}

        {/* Results Rendering Logic */}
        {msg.results?.length > 0 && (
          <div style={{marginTop: '20px'}}>
             <div style={{color: '#9ca3af', fontSize: '12px', marginBottom: '10px'}}>검색 결과 {msg.results.length}건</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageItem;
