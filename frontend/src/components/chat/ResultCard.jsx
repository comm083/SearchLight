import React, { useState } from 'react';
import { Clock } from 'lucide-react';

const ResultCard = ({ res, resultKey, isExpanded, setExpandedResults }) => {
  const [showVideoModal, setShowVideoModal] = useState(false);

  const hasClip = !!res.clip_url;

  return (
    <>
    <div className="result-card" style={{backgroundColor: '#0b0f19', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.05)', transition: 'all 0.3s ease'}}>
      <div style={{display: 'flex', gap: '15px', padding: '12px'}}>

        {/* 클립 영상 썸네일 영역 */}
        <div
          style={{width: '140px', height: '100px', borderRadius: '8px', overflow: 'hidden', flexShrink: 0, position: 'relative', cursor: hasClip ? 'pointer' : 'default', backgroundColor: '#1a1f2e'}}
          onClick={() => hasClip && setShowVideoModal(true)}
        >
          {hasClip ? (
            <video
              src={res.clip_url}
              style={{width: '100%', height: '100%', objectFit: 'cover'}}
              muted
              preload="metadata"
            />
          ) : (
            <div style={{width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#4b5563', fontSize: '11px'}}>
              클립 없음
            </div>
          )}
          <div style={{position: 'absolute', top: '5px', left: '5px', backgroundColor: 'rgba(0,0,0,0.7)', padding: '4px 8px', borderRadius: '12px', color: '#e5e7eb', fontSize: '10px', display: 'flex', alignItems: 'center', gap: '5px', fontWeight: '500', zIndex: 10, backdropFilter: 'blur(4px)'}}>
            <div style={{width: '6px', height: '6px', backgroundColor: '#ef4444', borderRadius: '50%', boxShadow: '0 0 4px #ef4444'}}></div>
            영상 녹화본
          </div>
          {hasClip && (
            <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.3)'}}>
              <div style={{width: '28px', height: '28px', borderRadius: '50%', backgroundColor: 'rgba(255,255,255,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <div style={{width: 0, height: 0, borderTop: '7px solid transparent', borderBottom: '7px solid transparent', borderLeft: '12px solid #111', marginLeft: '3px'}} />
              </div>
            </div>
          )}
          <div style={{position: 'absolute', bottom: '5px', right: '5px', backgroundColor: 'rgba(0,0,0,0.6)', padding: '2px 6px', borderRadius: '4px', fontSize: '10px', color: '#3b82f6'}}>{res.score ? (res.score * 100).toFixed(0) : '100'}%</div>
        </div>

        {/* 메타데이터 */}
        <div style={{flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}>
          <div>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px'}}>
              <div style={{fontSize: '11px', color: '#3b82f6', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px'}}><Clock size={10} /> {res.timestamp ? new Date(res.timestamp).toLocaleString('ko-KR') : '시간 정보 없음'}</div>
              <div style={{fontSize: '10px', color: '#6b7280'}}>{res.video_filename}</div>
            </div>
            {res.situation && res.situation !== 'normal' && (
              <div style={{display: 'inline-block', fontSize: '10px', padding: '2px 8px', borderRadius: '8px', backgroundColor: 'rgba(239,68,68,0.15)', color: '#f87171', marginBottom: '6px', fontWeight: 'bold'}}>
                {res.situation}
              </div>
            )}
            <div style={{fontSize: '13px', color: '#f3f4f6', lineHeight: '1.4', marginBottom: '8px'}}>{res.description}</div>
          </div>
        </div>
      </div>
    </div>

    {/* 클립 영상 모달 */}
    {showVideoModal && hasClip && (
      <div
        style={{position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', backgroundColor: 'rgba(0,0,0,0.9)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'zoom-out'}}
        onClick={() => setShowVideoModal(false)}
      >
        <video
          src={res.clip_url}
          style={{maxWidth: '90%', maxHeight: '85%', borderRadius: '8px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.5)'}}
          controls
          autoPlay
          onClick={e => e.stopPropagation()}
        />
        <div style={{position: 'absolute', bottom: '30px', color: '#9ca3af', fontSize: '14px', backgroundColor: 'rgba(0,0,0,0.5)', padding: '8px 16px', borderRadius: '20px'}}>
          아무 곳이나 클릭하여 닫기
        </div>
      </div>
    )}
    </>
  );
};

export default ResultCard;
