import React, { useState, useEffect, useRef } from 'react';
import { Play, MapPin, AlertTriangle, MoreVertical, Pencil, Trash2, ChevronLeft, ChevronRight, Check, X } from 'lucide-react';

const PendingVideos = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalUrl, setModalUrl] = useState(null);
  const [clipIndices, setClipIndices] = useState({});
  const [openMenuId, setOpenMenuId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState('');
  const menuRef = useRef(null);

  useEffect(() => {
    fetchPending();
  }, []);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpenMenuId(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchPending = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/alerts/events/pending?limit=100');
      if (res.ok) setEvents(await res.json());
    } catch (e) {
      console.error('처리대기 이벤트 조회 실패:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (eventId) => {
    if (!window.confirm('이 이벤트를 삭제하시겠습니까?')) return;
    setOpenMenuId(null);
    try {
      await fetch(`http://localhost:8000/api/alerts/events/${eventId}`, { method: 'DELETE' });
      setEvents(prev => prev.filter(e => e.id !== eventId));
    } catch {
      alert('삭제 중 오류가 발생했습니다.');
    }
  };

  const startEdit = (event) => {
    setOpenMenuId(null);
    setEditingId(event.id);
    const now = new Date();
    const pad = n => String(n).padStart(2, '0');
    setEditValue(`${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`);
  };

  const submitEdit = async (eventId) => {
    if (!editValue) return;
    const ts = editValue.replace('T', ' ') + ':00';
    try {
      const res = await fetch(`http://localhost:8000/api/alerts/events/${eventId}/timestamp`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ timestamp: ts }),
      });
      if (res.ok) {
        setEvents(prev => prev.filter(e => e.id !== eventId));
        setEditingId(null);
      } else {
        alert('업데이트 실패');
      }
    } catch {
      alert('네트워크 오류');
    }
  };

  const goClip = (eventId, dir, totalClips, e) => {
    e.stopPropagation();
    setClipIndices(prev => ({
      ...prev,
      [eventId]: Math.max(0, Math.min(totalClips - 1, (prev[eventId] ?? 0) + dir)),
    }));
  };

  return (
    <>
      <div style={{ padding: '30px 40px', maxWidth: '1200px', margin: '0 auto', width: '100%', color: '#f3f4f6' }}>
        <div style={{ marginBottom: '24px' }}>
          <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: '0 0 8px 0', color: '#fff' }}>처리대기 영상</h1>
          <p style={{ color: '#9ca3af', margin: 0, fontSize: '14px' }}>
            타임스탬프가 인식되지 않은 영상입니다. 직접 시각을 입력하거나 삭제할 수 있습니다.
          </p>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>불러오는 중...</div>
        ) : events.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px', color: '#6b7280', fontSize: '15px' }}>
            처리가 필요한 영상이 없습니다.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {events.map((event) => {
              const clips = (event.clips && event.clips.length > 0)
                ? event.clips
                : (event.clip_url ? [{ clip_url: event.clip_url, clip_index: 1 }] : []);
              const totalClips = clips.length;
              const curIdx = clipIndices[event.id] ?? 0;
              const curClip = clips[curIdx];
              const hasClip = !!curClip?.clip_url;
              const isAbnormal = event.tag && event.tag !== 'normal';
              const isEditing = editingId === event.id;
              const isMenuOpen = openMenuId === event.id;

              return (
                <div key={event.id} style={{ backgroundColor: '#1e293b', borderRadius: '12px', overflow: 'visible', display: 'flex', flexDirection: 'row', border: '1px solid #334155', position: 'relative' }}>
                  {/* 썸네일 */}
                  <div
                    style={{ width: '280px', height: '200px', position: 'relative', flexShrink: 0, cursor: hasClip ? 'pointer' : 'default', backgroundColor: '#0b0f19', borderRadius: '12px 0 0 12px', overflow: 'hidden' }}
                    onClick={() => hasClip && setModalUrl(curClip.clip_url)}
                  >
                    {hasClip ? (
                      <video key={curClip.clip_url} src={curClip.clip_url} style={{ width: '100%', height: '100%', objectFit: 'cover' }} muted preload="metadata" />
                    ) : (
                      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#4b5563', fontSize: '13px' }}>클립 없음</div>
                    )}
                    {hasClip && (
                      <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.25)' }}>
                        <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: 'rgba(255,255,255,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <div style={{ width: 0, height: 0, borderTop: '9px solid transparent', borderBottom: '9px solid transparent', borderLeft: '16px solid #111', marginLeft: '4px' }} />
                        </div>
                      </div>
                    )}
                    {isAbnormal && (
                      <div style={{ position: 'absolute', top: '12px', left: '12px', backgroundColor: 'rgba(239,68,68,0.85)', padding: '4px 10px', borderRadius: '20px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: '600', color: '#fff' }}>
                        <AlertTriangle size={11} /> {event.tag}
                      </div>
                    )}
                    {totalClips > 1 && (
                      <div style={{ position: 'absolute', bottom: '10px', right: '10px', backgroundColor: 'rgba(0,0,0,0.65)', color: '#e2e8f0', fontSize: '12px', fontWeight: '600', padding: '3px 8px', borderRadius: '12px' }}>
                        {curIdx + 1} / {totalClips}
                      </div>
                    )}
                  </div>

                  {/* 정보 영역 */}
                  <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
                    <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#fff', margin: '0 0 12px 0', lineHeight: '1.4', paddingRight: '32px' }}>{event.title}</h3>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#9ca3af', fontSize: '14px', marginBottom: '8px' }}>
                      <MapPin size={14} /> {event.location}
                    </div>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'rgba(234,179,8,0.12)', border: '1px solid rgba(234,179,8,0.3)', color: '#fbbf24', fontSize: '12px', fontWeight: '600', padding: '3px 10px', borderRadius: '20px', alignSelf: 'flex-start', marginBottom: 'auto' }}>
                      타임스탬프 미인식
                    </div>

                    {/* 타임스탬프 입력 폼 */}
                    {isEditing && (
                      <div style={{ marginTop: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <input
                          type="datetime-local"
                          value={editValue}
                          onChange={e => setEditValue(e.target.value)}
                          style={{ backgroundColor: '#0f172a', border: '1px solid #3b82f6', color: '#e2e8f0', borderRadius: '6px', padding: '6px 10px', fontSize: '13px', outline: 'none', colorScheme: 'dark' }}
                        />
                        <button
                          onClick={() => submitEdit(event.id)}
                          style={{ backgroundColor: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', padding: '6px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '13px', fontWeight: '600' }}
                        >
                          <Check size={14} /> 저장
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          style={{ backgroundColor: 'transparent', color: '#9ca3af', border: '1px solid #334155', borderRadius: '6px', padding: '6px 10px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                        >
                          <X size={14} />
                        </button>
                      </div>
                    )}

                    {/* 하단 액션 */}
                    <div style={{ display: 'flex', gap: '8px', marginTop: '20px', borderTop: '1px solid #334155', paddingTop: '20px', alignItems: 'center' }}>
                      <button
                        style={{ backgroundColor: hasClip ? '#60a5fa' : '#334155', color: hasClip ? '#0f172a' : '#6b7280', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px', cursor: hasClip ? 'pointer' : 'not-allowed', fontSize: '13px' }}
                        onClick={() => hasClip && setModalUrl(curClip.clip_url)}
                        disabled={!hasClip}
                      >
                        <Play size={14} /> 영상 보기
                      </button>

                      {totalClips > 1 && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginLeft: '8px' }}>
                          <button onClick={(e) => goClip(event.id, -1, totalClips, e)} disabled={curIdx === 0} style={{ background: 'none', border: '1px solid #334155', color: curIdx === 0 ? '#4b5563' : '#9ca3af', borderRadius: '4px', width: '28px', height: '28px', cursor: curIdx === 0 ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <ChevronLeft size={14} />
                          </button>
                          <span style={{ fontSize: '12px', color: '#9ca3af', minWidth: '48px', textAlign: 'center' }}>클립 {curIdx + 1}/{totalClips}</span>
                          <button onClick={(e) => goClip(event.id, 1, totalClips, e)} disabled={curIdx === totalClips - 1} style={{ background: 'none', border: '1px solid #334155', color: curIdx === totalClips - 1 ? '#4b5563' : '#9ca3af', borderRadius: '4px', width: '28px', height: '28px', cursor: curIdx === totalClips - 1 ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <ChevronRight size={14} />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 점 3개 메뉴 */}
                  <div style={{ position: 'absolute', top: '16px', right: '16px' }} ref={isMenuOpen ? menuRef : null}>
                    <button
                      onClick={(e) => { e.stopPropagation(); setOpenMenuId(isMenuOpen ? null : event.id); }}
                      style={{ background: 'none', border: 'none', color: '#6b7280', cursor: 'pointer', padding: '4px', borderRadius: '4px', display: 'flex', alignItems: 'center' }}
                    >
                      <MoreVertical size={18} />
                    </button>
                    {isMenuOpen && (
                      <div style={{ position: 'absolute', top: '28px', right: 0, backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px', boxShadow: '0 8px 24px rgba(0,0,0,0.5)', zIndex: 100, minWidth: '130px', overflow: 'hidden' }}>
                        <button
                          onClick={() => startEdit(event)}
                          style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', background: 'none', border: 'none', color: '#e2e8f0', cursor: 'pointer', fontSize: '13px', textAlign: 'left' }}
                          onMouseEnter={e => e.currentTarget.style.backgroundColor = '#1e293b'}
                          onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                        >
                          <Pencil size={14} /> 입력
                        </button>
                        <button
                          onClick={() => handleDelete(event.id)}
                          style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 16px', background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', fontSize: '13px', textAlign: 'left' }}
                          onMouseEnter={e => e.currentTarget.style.backgroundColor = '#1e293b'}
                          onMouseLeave={e => e.currentTarget.style.backgroundColor = 'transparent'}
                        >
                          <Trash2 size={14} /> 삭제
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 영상 모달 */}
      {modalUrl && (
        <div
          style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', backgroundColor: 'rgba(0,0,0,0.92)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'zoom-out' }}
          onClick={() => setModalUrl(null)}
        >
          <video
            src={modalUrl}
            style={{ maxWidth: '90%', maxHeight: '85%', borderRadius: '10px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.5)' }}
            controls autoPlay
            onClick={e => e.stopPropagation()}
          />
          <div style={{ position: 'absolute', bottom: '30px', color: '#9ca3af', fontSize: '14px', backgroundColor: 'rgba(0,0,0,0.5)', padding: '8px 16px', borderRadius: '20px' }}>
            아무 곳이나 클릭하여 닫기
          </div>
        </div>
      )}
    </>
  );
};

export default PendingVideos;
