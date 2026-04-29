import React, { useState } from 'react';
import { Shield, AlertCircle, Clock, Play, Video, XCircle } from 'lucide-react';

/**
 * 검색 결과 카드 한 개를 렌더링하는 서브 컴포넌트
 */
const ResultCard = ({ res, msgIdx, resIdx }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showVideo, setShowVideo] = useState(false);
  const resultKey = `${msgIdx}-${resIdx}`;

  return (
    <div className="result-card" style={{ backgroundColor: '#0b0f19', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.05)', transition: 'all 0.3s ease' }}>
      <div style={{ display: 'flex', gap: '15px', padding: '12px' }}>
        <div style={{ width: '140px', height: '100px', borderRadius: '8px', overflow: 'hidden', flexShrink: 0, position: 'relative' }}>
          <img src={`http://localhost:8000${res.image_path}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="cctv thumb" />
          <div style={{ position: 'absolute', bottom: '5px', right: '5px', backgroundColor: 'rgba(0,0,0,0.6)', padding: '2px 6px', borderRadius: '4px', fontSize: '10px', color: '#3b82f6' }}>
            {(res.score).toFixed(0)}%
          </div>
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
              <div style={{ fontSize: '11px', color: '#3b82f6', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={10} /> {res.timestamp ? new Date(res.timestamp).toLocaleString('ko-KR') : '시간 정보 없음'}
              </div>
              <div style={{ fontSize: '10px', color: '#6b7280' }}>{res.video_filename}</div>
            </div>
            <div style={{ fontSize: '13px', color: '#f3f4f6', lineHeight: '1.4', marginBottom: '8px' }}>{res.description}</div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            {res.detections?.length > 0 && (
              <button onClick={() => setIsExpanded(prev => !prev)}
                style={{ background: 'rgba(59,130,246,0.1)', border: 'none', color: '#60a5fa', fontSize: '11px', padding: '4px 10px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
                {isExpanded ? '정보 접기' : '상세 정보'}
              </button>
            )}
            <button onClick={() => setShowVideo(prev => !prev)}
              style={{ background: 'rgba(239,68,68,0.1)', border: 'none', color: '#f87171', fontSize: '11px', padding: '4px 10px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
              {showVideo ? <XCircle size={12} /> : <Play size={12} />}
              {showVideo ? '영상 닫기' : '영상 재생'}
            </button>
          </div>
        </div>
      </div>

      {showVideo && (
        <div style={{ padding: '15px', borderTop: '1px solid rgba(255,255,255,0.05)', backgroundColor: '#000' }}>
          <video 
            src={`http://localhost:8000${res.video_url}`} 
            controls 
            autoPlay 
            style={{ width: '100%', borderRadius: '8px', boxShadow: '0 4px 15px rgba(0,0,0,0.5)' }}
          />
        </div>
      )}

      {isExpanded && res.detections?.length > 0 && (
        <div style={{ padding: '0 15px 15px', borderTop: '1px solid rgba(255,255,255,0.05)', backgroundColor: 'rgba(255,255,255,0.02)' }}>
          <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '12px', position: 'relative' }}>
            <div style={{ position: 'absolute', left: '75px', top: '5px', bottom: '5px', width: '2px', backgroundColor: 'rgba(59,130,246,0.2)' }}></div>
            {res.detections.map((det, k) => {
              const timeStr = det.time?.includes('T')
                ? det.time.split('T')[1].split('.')[0]
                : (det.time?.includes(' ') ? det.time.split(' ')[1] : det.time);
              return (
                <div key={k} style={{ display: 'flex', gap: '20px', alignItems: 'center', fontSize: '12px', position: 'relative', zIndex: 1 }}>
                  <div style={{ color: '#3b82f6', fontWeight: 'bold', whiteSpace: 'nowrap', width: '60px', textAlign: 'right' }}>{timeStr}</div>
                  <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#3b82f6', border: '2px solid #0b0f19', marginLeft: '-5px' }}></div>
                  <div style={{ color: '#d1d5db', lineHeight: '1.4', backgroundColor: 'rgba(255,255,255,0.05)', padding: '6px 12px', borderRadius: '8px', flex: 1 }}>{det.description}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * AI 메시지 버블 (보고서 + 검색 결과)
 */
const AiMessageBubble = ({ msg, msgIdx, viewMode }) => (
  <div style={{ width: '100%', backgroundColor: msg.intent === 'ERROR' ? '#450a0a' : '#1a2235', padding: '25px', borderRadius: '15px', border: msg.intent === 'ERROR' ? '1px solid #ef4444' : '1px solid rgba(255,255,255,0.1)' }}>
    {/* 헤더 */}
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px', color: msg.intent === 'ERROR' ? '#f87171' : '#3b82f6', fontSize: '13px', fontWeight: 'bold' }}>
      {msg.intent === 'ERROR' ? <AlertCircle size={16} /> : <Shield size={16} />}
      {msg.intent === 'ERROR' ? '시스템 오류' : 'AI 분석 보고서'}
      <span style={{ flex: 1 }}></span>
      <span style={{ fontSize: '10px', color: '#6b7280' }}>{msg.intent}</span>
    </div>

    {/* 보고서 본문 */}
    <div style={{ fontSize: '14px', lineHeight: '1.7', color: '#d1d5db', whiteSpace: 'pre-wrap', backgroundColor: 'rgba(255,255,255,0.03)', padding: '15px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.05)' }}>
      {msg.mode === 'flash' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'inline-flex', alignSelf: 'flex-start', padding: '2px 8px', backgroundColor: 'rgba(59,130,246,0.2)', color: '#60a5fa', borderRadius: '4px', fontSize: '10px', fontWeight: '800', border: '1px solid rgba(59,130,246,0.3)', marginBottom: '5px' }}>
            ⚡ 특정 시점 상황 분석
          </div>
          <div style={{ fontSize: '15px', color: '#f3f4f6', fontWeight: '500' }}>{msg.report}</div>
        </div>
      ) : msg.report}
    </div>

    {/* 검색 결과 */}
    {msg.results?.length > 0 && (
      <div style={{ marginTop: '20px' }}>
        {viewMode === 'list' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            {msg.results.map((res, j) => (
              <ResultCard key={j} res={res} msgIdx={msgIdx} resIdx={j} />
            ))}
          </div>
        ) : (
          <div style={{ backgroundColor: '#0b0f19', borderRadius: '15px', height: '300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: '2px dashed rgba(59,130,246,0.3)', gap: '15px' }}>
            <div style={{ fontSize: '40px' }}>🗺️</div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: 'white', marginBottom: '5px' }}>건물 도면 기반 위치 확인 중</div>
              <div style={{ fontSize: '14px', color: '#6b7280' }}>감지된 이벤트 {msg.results.length}건이 지도에 표시됩니다.</div>
            </div>
            <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
              {msg.results.map((_, idx) => (
                <div key={idx} style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#ef4444', boxShadow: '0 0 10px #ef4444' }}></div>
              ))}
            </div>
          </div>
        )}
      </div>
    )}
  </div>
);

/**
 * 채팅 메시지 영역 전체
 */
const ChatArea = ({ messages, loading, chatEndRef, viewMode }) => (
  <div className="chat-container" style={{ flex: 1, overflowY: 'auto', padding: '40px' }}>
    {messages.length === 0 ? (
      <div className="welcome-screen" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <h1 className="welcome-title" style={{ fontSize: '28px', textAlign: 'center', lineHeight: '1.5', fontWeight: '300' }}>
          지능형 보안 분석관 <span style={{ fontWeight: '700', color: '#3b82f6' }}>SearchLight</span>입니다.<br />
          <span style={{ fontSize: '18px', color: '#9ca3af' }}>CCTV 분석 및 보안 관련 질문을 입력하세요.</span>
        </h1>
      </div>
    ) : (
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ marginBottom: '30px', display: 'flex', flexDirection: 'column', alignItems: msg.type === 'user' ? 'flex-end' : 'flex-start' }}>
            {msg.type === 'user' ? (
              <div style={{ backgroundColor: '#3b82f6', padding: '12px 20px', borderRadius: '15px 15px 0 15px', maxWidth: '80%', fontSize: '14px' }}>{msg.text}</div>
            ) : (
              <AiMessageBubble msg={msg} msgIdx={i} viewMode={viewMode} />
            )}
          </div>
        ))}
        {loading && <div style={{ color: '#3b82f6', fontSize: '12px', fontStyle: 'italic' }}>AI 분석 중...</div>}
        <div ref={chatEndRef} />
      </div>
    )}
  </div>
);

export default ChatArea;
