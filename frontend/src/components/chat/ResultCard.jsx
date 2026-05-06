import React, { useState } from 'react';
import { Clock, Maximize2 } from 'lucide-react';

const ResultCard = ({ res, resultKey, isExpanded, setExpandedResults }) => {
  const [showImageModal, setShowImageModal] = useState(false);

  return (
    <>
    <div className="result-card" style={{backgroundColor: '#0b0f19', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.05)', transition: 'all 0.3s ease'}}>
      <div style={{display: 'flex', gap: '15px', padding: '12px'}}>
        <div 
          style={{width: '140px', height: '100px', borderRadius: '8px', overflow: 'hidden', flexShrink: 0, position: 'relative', cursor: 'pointer'}}
          onClick={() => setShowImageModal(true)}
        >
          <img src={`http://localhost:8000${res.image_path}`} style={{width: '100%', height: '100%', objectFit: 'cover', transition: 'transform 0.2s'}} onMouseOver={e => e.currentTarget.style.transform='scale(1.05)'} onMouseOut={e => e.currentTarget.style.transform='scale(1)'} alt="cctv thumb" />
          <div style={{position: 'absolute', top: '5px', left: '5px', backgroundColor: 'rgba(0,0,0,0.7)', padding: '4px 8px', borderRadius: '12px', color: '#e5e7eb', fontSize: '10px', display: 'flex', alignItems: 'center', gap: '5px', fontWeight: '500', zIndex: 10, backdropFilter: 'blur(4px)'}}>
            <div style={{width: '6px', height: '6px', backgroundColor: '#ef4444', borderRadius: '50%', boxShadow: '0 0 4px #ef4444'}}></div>
            영상 녹화본
          </div>
          <div style={{position: 'absolute', bottom: '5px', right: '5px', backgroundColor: 'rgba(0,0,0,0.6)', padding: '2px 6px', borderRadius: '4px', fontSize: '10px', color: '#3b82f6'}}>{res.score ? (res.score * 100).toFixed(0) : '100'}%</div>
        </div>
        <div style={{flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}>
          <div>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px'}}>
              <div style={{fontSize: '11px', color: '#3b82f6', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px'}}><Clock size={10} /> {res.timestamp ? new Date(res.timestamp).toLocaleString('ko-KR') : '시간 정보 없음'}</div>
              <div style={{fontSize: '10px', color: '#6b7280'}}>{res.video_filename}</div>
            </div>
            <div style={{fontSize: '13px', color: '#f3f4f6', lineHeight: '1.4', marginBottom: '8px'}}>{res.description}</div>
          </div>
          {res.frames?.length > 0 && (
            <button 
              onClick={() => setExpandedResults(prev => ({...prev, [resultKey]: !prev[resultKey]}))}
              style={{background: 'rgba(59, 130, 246, 0.1)', border: 'none', color: '#60a5fa', fontSize: '11px', padding: '4px 10px', borderRadius: '6px', cursor: 'pointer', alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: '4px'}}
            >
              {isExpanded ? '상세 정보 접기' : `${res.frames.length}개의 상세 프레임 보기`}
            </button>
          )}
        </div>
      </div>
      
      {isExpanded && res.frames?.length > 0 && (
        <div style={{padding: '0 15px 15px', borderTop: '1px solid rgba(255,255,255,0.05)', backgroundColor: 'rgba(255,255,255,0.02)'}}>
          <div style={{marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '12px', position: 'relative'}}>
            <div style={{position: 'absolute', left: '75px', top: '5px', bottom: '5px', width: '2px', backgroundColor: 'rgba(59, 130, 246, 0.2)'}}></div>
            {res.frames.map((f, k) => (
              <div key={k} style={{display: 'flex', gap: '20px', alignItems: 'center', fontSize: '12px', position: 'relative', zIndex: 1}}>
                <div style={{color: '#3b82f6', fontWeight: 'bold', whiteSpace: 'nowrap', width: '60px', textAlign: 'right'}}>{f.timestamp || f.time}</div>
                <div style={{width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#3b82f6', border: '2px solid #0b0f19', marginLeft: '-5px'}}></div>
                <div style={{color: '#d1d5db', lineHeight: '1.4', backgroundColor: 'rgba(255,255,255,0.05)', padding: '6px 12px', borderRadius: '8px', flex: 1}}>{f.notes || f.person || f.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>

    {showImageModal && (
      <div 
        style={{position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', backgroundColor: 'rgba(0,0,0,0.85)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'zoom-out'}}
        onClick={() => setShowImageModal(false)}
      >
        <img 
          src={`http://localhost:8000${res.image_path}`} 
          style={{maxWidth: '90%', maxHeight: '90%', objectFit: 'contain', borderRadius: '8px', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'}} 
          alt="Enlarged cctv frame" 
        />
        <div style={{position: 'absolute', bottom: '40px', color: '#9ca3af', fontSize: '14px', backgroundColor: 'rgba(0,0,0,0.5)', padding: '8px 16px', borderRadius: '20px'}}>
          아무 곳이나 클릭하여 닫기
        </div>
      </div>
    )}
    </>
  );
};

export default ResultCard;
