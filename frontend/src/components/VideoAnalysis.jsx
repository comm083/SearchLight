import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Upload, Film, X, Play, Loader, CheckCircle, AlertCircle, FolderOpen } from 'lucide-react';

const formatDuration = (sec) => {
  if (!sec || isNaN(sec)) return '--:--';
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
};

const getVideoDuration = (file) =>
  new Promise((resolve) => {
    const video = document.createElement('video');
    video.preload = 'metadata';
    video.onloadedmetadata = () => { resolve(video.duration); URL.revokeObjectURL(video.src); };
    video.onerror = () => resolve(0);
    video.src = URL.createObjectURL(file);
  });

const StatusIcon = ({ status }) => {
  if (status === 'running') return <Loader size={16} className="spin" style={{ color: '#60a5fa' }} />;
  if (status === 'done')    return <CheckCircle size={16} style={{ color: '#4ade80' }} />;
  if (status === 'error')   return <AlertCircle size={16} style={{ color: '#f87171' }} />;
  return <div style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid #4b5563' }} />;
};

const statusLabel = { pending: '대기 중', running: '분석 중...', done: '완료', error: '오류' };
const statusColor = { pending: '#9ca3af', running: '#60a5fa', done: '#4ade80', error: '#f87171' };

const VideoAnalysis = () => {
  const [videos, setVideos]       = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [jobs, setJobs]           = useState({});
  const [jobIds, setJobIds]       = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const fileInputRef = useRef(null);
  const pollRef      = useRef(null);

  const addFiles = async (fileList) => {
    const incoming = [];
    for (const file of fileList) {
      if (!file.type.startsWith('video/') && !file.name.match(/\.(mp4|avi|mov|mkv|wmv|flv|webm)$/i)) continue;
      const duration = await getVideoDuration(file);
      incoming.push({ file, id: crypto.randomUUID(), name: file.name, duration });
    }
    if (incoming.length) setVideos((prev) => [...prev, ...incoming]);
  };

  const handleDrop = useCallback(async (e) => {
    e.preventDefault();
    setIsDragging(false);
    await addFiles(Array.from(e.dataTransfer.files));
  }, []);

  const handleDragOver  = (e) => { e.preventDefault(); setIsDragging(true);  };
  const handleDragLeave = ()  => setIsDragging(false);
  const handleFileChange = async (e) => { await addFiles(Array.from(e.target.files)); e.target.value = ''; };
  const removeVideo = (id) => setVideos((prev) => prev.filter((v) => v.id !== id));

  const startAnalysis = async () => {
    setIsAnalyzing(true);
    setJobs({});
    setJobIds([]);

    const formData = new FormData();
    videos.forEach((v) => formData.append('files', v.file, v.name));

    try {
      const res  = await fetch('http://localhost:8000/api/alerts/analyze', { method: 'POST', body: formData });
      const data = await res.json();
      const ids  = data.jobs.map((j) => j.job_id);
      setJobIds(ids);
      const init = {};
      data.jobs.forEach((j) => { init[j.job_id] = { status: 'pending', filename: j.filename, progress: '대기 중' }; });
      setJobs(init);
    } catch (e) {
      console.error('분석 요청 실패:', e);
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    if (!jobIds.length) return;
    const poll = async () => {
      try {
        const res  = await fetch(`http://localhost:8000/api/alerts/analyze/status?job_ids=${jobIds.join(',')}`);
        const data = await res.json();
        setJobs(data);
        const allDone = Object.values(data).every((j) => j.status === 'done' || j.status === 'error');
        if (allDone) { clearInterval(pollRef.current); setIsAnalyzing(false); }
      } catch {}
    };
    poll();
    pollRef.current = setInterval(poll, 3000);
    return () => clearInterval(pollRef.current);
  }, [jobIds]);

  const hasVideos  = videos.length > 0;
  const allDone    = jobIds.length > 0 && Object.values(jobs).every((j) => j.status === 'done' || j.status === 'error');
  const jobByName  = Object.fromEntries(Object.entries(jobs).map(([, v]) => [v.filename, v]));

  return (
    <div style={{ padding: '32px', maxWidth: '1200px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#f9fafb', marginBottom: '6px' }}>영상 분석</h2>
      <p style={{ color: '#6b7280', fontSize: '13px', marginBottom: '28px' }}>
        분석할 영상을 불러온 뒤 분석을 시작하세요. 분석 결과는 영상 보관함에 자동으로 저장됩니다.
      </p>

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        style={{
          height: '480px',
          width: 'auto',
          aspectRatio: '16 / 9',
          border: `2px dashed ${isDragging ? '#3b82f6' : hasVideos ? 'rgba(59,130,246,0.3)' : 'rgba(75,85,99,0.5)'}`,
          borderRadius: '16px',
          backgroundColor: isDragging ? 'rgba(59,130,246,0.07)' : 'rgba(17,24,39,0.8)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: hasVideos ? 'flex-start' : 'center',
          padding: hasVideos ? '20px' : '48px 20px',
          transition: 'all 0.2s',
          position: 'relative',
          overflow: 'hidden',
          boxSizing: 'border-box',
        }}
      >
        {/* Empty state */}
        {!hasVideos && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', pointerEvents: 'none' }}>
            <div style={{ width: '64px', height: '64px', borderRadius: '14px', backgroundColor: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Upload size={28} color="#3b82f6" />
            </div>
            <p style={{ color: '#d1d5db', fontSize: '15px', fontWeight: '500', margin: 0 }}>드래그해서 영상 가져오기</p>
            <p style={{ color: '#6b7280', fontSize: '12px', margin: 0 }}>MP4, AVI, MOV, MKV 등 지원 · 여러 파일 동시 가능</p>
          </div>
        )}

        {/* Video list */}
        {hasVideos && (
          <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {videos.map((v) => {
              const job = jobByName[v.name];
              return (
                <div key={v.id} style={{ display: 'flex', alignItems: 'center', gap: '12px', backgroundColor: 'rgba(30,41,59,0.8)', borderRadius: '10px', padding: '12px 14px', border: '1px solid rgba(59,130,246,0.1)' }}>
                  <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: 'rgba(59,130,246,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Film size={18} color="#60a5fa" />
                  </div>
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#f1f5f9', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{v.name}</div>
                    <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span>길이 {formatDuration(v.duration)}</span>
                      {job && (
                        <>
                          <span style={{ color: '#374151' }}>·</span>
                          <span style={{ color: statusColor[job.status] || '#9ca3af' }}>{statusLabel[job.status] || job.progress}</span>
                        </>
                      )}
                    </div>
                  </div>
                  {job ? (
                    <StatusIcon status={job.status} />
                  ) : (
                    !isAnalyzing && (
                      <button onClick={() => removeVideo(v.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#4b5563', padding: '4px', display: 'flex', borderRadius: '6px' }}
                        onMouseEnter={(e) => (e.currentTarget.style.color = '#f87171')}
                        onMouseLeave={(e) => (e.currentTarget.style.color = '#4b5563')}
                      >
                        <X size={16} />
                      </button>
                    )
                  )}
                </div>
              );
            })}

            {/* Drop more hint (when files exist) */}
            {!isAnalyzing && (
              <div style={{ textAlign: 'center', color: '#4b5563', fontSize: '12px', padding: '8px 0' }}>
                여기에 영상을 더 드래그하거나 아래 버튼으로 추가할 수 있습니다
              </div>
            )}
          </div>
        )}

      </div>

      {/* All done banner */}
      {allDone && (
        <div style={{ marginTop: '16px', padding: '12px 16px', borderRadius: '10px', backgroundColor: 'rgba(74,222,128,0.08)', border: '1px solid rgba(74,222,128,0.2)', color: '#4ade80', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={16} />
          분석이 완료되었습니다. 영상 보관함에서 결과를 확인하세요.
        </div>
      )}

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: '12px', marginTop: '20px', justifyContent: 'center' }}>
        <input ref={fileInputRef} type="file" accept="video/*" multiple style={{ display: 'none' }} onChange={handleFileChange} />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isAnalyzing}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', borderRadius: '10px', border: '1px solid rgba(59,130,246,0.3)', backgroundColor: 'rgba(59,130,246,0.08)', color: '#60a5fa', fontSize: '13px', fontWeight: '600', cursor: isAnalyzing ? 'not-allowed' : 'pointer', opacity: isAnalyzing ? 0.5 : 1, transition: 'all 0.15s' }}
          onMouseEnter={(e) => { if (!isAnalyzing) e.currentTarget.style.backgroundColor = 'rgba(59,130,246,0.15)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'rgba(59,130,246,0.08)'; }}
        >
          <FolderOpen size={16} />
          영상 불러오기
        </button>
        <button
          onClick={startAnalysis}
          disabled={!hasVideos || isAnalyzing}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 24px', borderRadius: '10px', border: 'none', backgroundColor: hasVideos && !isAnalyzing ? '#3b82f6' : 'rgba(59,130,246,0.2)', color: hasVideos && !isAnalyzing ? '#fff' : '#4b5563', fontSize: '13px', fontWeight: '600', cursor: hasVideos && !isAnalyzing ? 'pointer' : 'not-allowed', transition: 'all 0.15s' }}
          onMouseEnter={(e) => { if (hasVideos && !isAnalyzing) e.currentTarget.style.backgroundColor = '#2563eb'; }}
          onMouseLeave={(e) => { if (hasVideos && !isAnalyzing) e.currentTarget.style.backgroundColor = '#3b82f6'; }}
        >
          {isAnalyzing ? <><Loader size={16} className="spin" /> 분석 중...</> : <><Play size={16} /> 영상 분석하기</>}
        </button>
      </div>

      <style>{`
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

export default VideoAnalysis;
