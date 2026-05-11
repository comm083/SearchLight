import React, { useState, useEffect } from 'react';
import { Search, Download, Play, MapPin, Clock, AlertTriangle, ChevronLeft, ChevronRight, Trash2, Lock } from 'lucide-react';

const formatCctvTime = (ts) => {
  if (!ts) return '';
  const clean = ts.replace('T', ' ').replace(/\.\d+/, '').replace(/([+-]\d{2}:\d{2}|Z)$/, '');
  const [date, time] = clean.split(' ');
  if (!date) return ts;
  const [y, m, d] = date.split('-');
  if (!time) return `${y}. ${parseInt(m)}. ${parseInt(d)}.`;
  const [hh, mi, ss] = time.split(':');
  const hour = parseInt(hh);
  const ampm = hour < 12 ? '오전' : '오후';
  const h12 = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
  return `${y}. ${parseInt(m)}. ${parseInt(d)}. ${ampm} ${h12}:${mi}:${ss || '00'}`;
};

const getRawDate = (ts) => {
  if (!ts) return '';
  return ts.replace('T', ' ').replace(/\.\d+/, '').replace(/([+-]\d{2}:\d{2}|Z)$/, '').split(' ')[0];
};

// YYYY-MM-DD 문자열 → Date (로컬 기준, timezone 변환 없음)
const parseLocalDate = (dateStr) => {
  const [y, m, d] = dateStr.split('-').map(Number);
  return new Date(y, m - 1, d);
};

const toDateStr = (date) => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

const getWeekRange = (dateStr) => {
  const d = parseLocalDate(dateStr);
  const day = d.getDay(); // 0=일, 1=월 ...
  const mon = new Date(d); mon.setDate(d.getDate() - ((day + 6) % 7));
  const sun = new Date(mon); sun.setDate(mon.getDate() + 6);
  return { start: toDateStr(mon), end: toDateStr(sun) };
};

const VIEW_MODES = [
  { label: '일별', value: 'daily' },
  { label: '주간', value: 'weekly' },
  { label: '월별', value: 'monthly' },
];

const EventHistory = ({ user }) => {
  const isAdmin = user?.role === '관리자';

  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('daily');
  const [anchorDate, setAnchorDate] = useState(() => toDateStr(new Date()));
  const [modalUrl, setModalUrl] = useState(null);
  // 이벤트별 현재 선택된 클립 인덱스 (eventId → clipArrayIndex)
  const [clipIndices, setClipIndices] = useState({});

  useEffect(() => { fetchEvents(); }, []);

  const fetchEvents = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/alerts/events?limit=300');
      if (response.ok) {
        const data = await response.json();
        setEvents(data);
        setFetchError(null);
      } else {
        setFetchError(`서버 오류: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to fetch events:', error);
      setFetchError(`네트워크 오류: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // anchorDate 기준 범위 계산
  const getRange = () => {
    if (viewMode === 'daily') {
      return { start: anchorDate, end: anchorDate };
    }
    if (viewMode === 'weekly') {
      return getWeekRange(anchorDate);
    }
    // monthly
    const [y, m] = anchorDate.split('-').map(Number);
    const lastDay = new Date(y, m, 0).getDate();
    return {
      start: `${String(y)}-${String(m).padStart(2, '0')}-01`,
      end:   `${String(y)}-${String(m).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`,
    };
  };

  const { start, end } = getRange();

  const filteredEvents = events.filter(e => {
    const matchesSearch = (e.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (e.location || '').toLowerCase().includes(searchTerm.toLowerCase());
    if (!matchesSearch) return false;
    const d = getRawDate(e.timestamp);
    if (!d) return false;
    return d >= start && d <= end;
  });

  // 이전/다음 이동
  const navigate = (dir) => {
    const d = parseLocalDate(anchorDate);
    if (viewMode === 'daily') {
      d.setDate(d.getDate() + dir);
    } else if (viewMode === 'weekly') {
      d.setDate(d.getDate() + dir * 7);
    } else {
      d.setMonth(d.getMonth() + dir);
    }
    setAnchorDate(toDateStr(d));
  };

  // 범위 레이블
  const rangeLabel = () => {
    if (viewMode === 'daily') return anchorDate;
    if (viewMode === 'weekly') return `${start} ~ ${end}`;
    const [y, m] = anchorDate.split('-');
    return `${y}년 ${parseInt(m)}월`;
  };

  const handleDelete = async (eventId) => {
    if (!window.confirm('이 이벤트를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return;
    try {
      await fetch(`http://localhost:8000/api/alerts/events/${eventId}`, { method: 'DELETE' });
      setEvents(prev => prev.filter(e => e.id !== eventId));
    } catch (err) {
      alert('삭제 중 오류가 발생했습니다.');
    }
  };

  const handleDownload = () => {
    if (filteredEvents.length === 0) { alert("다운로드할 이벤트가 없습니다."); return; }
    const headers = ["ID", "이벤트 내용", "위치", "발생 시각", "상황"];
    const csvRows = filteredEvents.map(e => [
      e.id || '',
      `"${(e.title || '').replace(/"/g, '""')}"`,
      `"${e.location || ''}"`,
      `"${e.timestamp || ''}"`,
      e.tag || '',
    ].join(','));
    const csvContent = "﻿" + headers.join(',') + "\n" + csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `보안이벤트_보고서_${anchorDate}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <>
      <div style={{ padding: '30px 40px', maxWidth: '1200px', margin: '0 auto', width: '100%', color: '#f3f4f6' }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: '0 0 8px 0', color: '#fff' }}>영상 보관함</h1>
            <p style={{ color: '#9ca3af', margin: 0, fontSize: '14px' }}>감지된 모든 보안 이벤트 영상을 조회하고 검색합니다.</p>
          </div>
          {isAdmin ? (
            <button
              style={{ backgroundColor: '#60a5fa', color: '#0f172a', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px' }}
              onClick={handleDownload}
            >
              <Download size={16} /> 다운로드
            </button>
          ) : (
            <div title="관리자만 다운로드할 수 있습니다" style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#4b5563', fontSize: '13px', padding: '8px 16px', borderRadius: '6px', border: '1px solid #1e293b', cursor: 'not-allowed' }}>
              <Lock size={14} /> 다운로드
            </div>
          )}
        </div>

        {/* 뷰 모드 탭 + 날짜 네비게이터 + 검색 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>

          {/* 탭 + 날짜 네비게이터 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* 뷰 모드 탭 */}
            <div style={{ display: 'flex', backgroundColor: '#1e293b', borderRadius: '8px', padding: '4px', border: '1px solid #334155' }}>
              {VIEW_MODES.map(({ label, value }) => (
                <button
                  key={value}
                  onClick={() => setViewMode(value)}
                  style={{
                    padding: '6px 16px', borderRadius: '6px', border: 'none', cursor: 'pointer',
                    fontSize: '13px', fontWeight: '600',
                    backgroundColor: viewMode === value ? '#3b82f6' : 'transparent',
                    color: viewMode === value ? '#fff' : '#9ca3af',
                    transition: 'all 0.15s',
                  }}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* 날짜 네비게이터 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '4px 8px' }}>
              <button
                onClick={() => navigate(-1)}
                style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '4px' }}
              >
                <ChevronLeft size={18} />
              </button>
              <span style={{ fontSize: '14px', fontWeight: '600', color: '#e2e8f0', minWidth: viewMode === 'weekly' ? '200px' : '110px', textAlign: 'center' }}>
                {rangeLabel()}
              </span>
              <button
                onClick={() => navigate(1)}
                style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '4px' }}
              >
                <ChevronRight size={18} />
              </button>
            </div>

            {/* 일별일 때 날짜 직접 선택 */}
            {viewMode === 'daily' && (
              <input
                type="date"
                value={anchorDate}
                onChange={(e) => e.target.value && setAnchorDate(e.target.value)}
                style={{
                  backgroundColor: '#1e293b', border: '1px solid #334155', color: '#9ca3af',
                  padding: '8px 12px', borderRadius: '8px', cursor: 'pointer',
                  fontFamily: 'inherit', fontSize: '13px', outline: 'none', colorScheme: 'dark',
                }}
              />
            )}
            {/* 월별일 때 월 선택 */}
            {viewMode === 'monthly' && (
              <input
                type="month"
                value={anchorDate.slice(0, 7)}
                onChange={(e) => e.target.value && setAnchorDate(`${e.target.value}-01`)}
                style={{
                  backgroundColor: '#1e293b', border: '1px solid #334155', color: '#9ca3af',
                  padding: '8px 12px', borderRadius: '8px', cursor: 'pointer',
                  fontFamily: 'inherit', fontSize: '13px', outline: 'none', colorScheme: 'dark',
                }}
              />
            )}
          </div>

          {/* 검색 */}
          <div style={{ position: 'relative' }}>
            <Search size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: '#6b7280' }} />
            <input
              type="text"
              placeholder="상황 설명, 위치 또는 카메라 이름으로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ width: '100%', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '12px 16px 12px 42px', color: '#fff', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }}
            />
          </div>
        </div>

        {/* 이벤트 수 */}
        <div style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '16px', paddingBottom: '16px', borderBottom: '1px solid #1e293b' }}>
          {rangeLabel()} · 총 {filteredEvents.length}개의 이벤트
        </div>

        {fetchError && (
          <div style={{ backgroundColor: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: '8px', padding: '12px 16px', marginBottom: '16px', color: '#f87171', fontSize: '14px' }}>
            ⚠️ {fetchError}
          </div>
        )}

        {/* 이벤트 목록 */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>이벤트를 불러오는 중입니다...</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {filteredEvents.map((event, idx) => {
              const clips = (event.clips && event.clips.length > 0)
                ? event.clips
                : (event.clip_url ? [{ clip_url: event.clip_url, clip_index: 1 }] : []);
              const totalClips = clips.length;
              const curClipIdx = clipIndices[event.id] ?? 0;
              const curClip = clips[curClipIdx];
              const hasClip = !!curClip?.clip_url;
              const isAbnormal = event.tag && event.tag !== 'normal';

              const goClip = (dir, e) => {
                e.stopPropagation();
                setClipIndices(prev => ({
                  ...prev,
                  [event.id]: Math.max(0, Math.min(totalClips - 1, (prev[event.id] ?? 0) + dir)),
                }));
              };

              return (
                <div key={idx} style={{ backgroundColor: '#1e293b', borderRadius: '12px', overflow: 'hidden', display: 'flex', flexDirection: 'row', border: '1px solid #334155' }}>
                  {/* 썸네일 영역 */}
                  <div
                    style={{ width: '280px', height: '200px', position: 'relative', flexShrink: 0, cursor: hasClip ? 'pointer' : 'default', backgroundColor: '#0b0f19' }}
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
                    {/* 클립 번호 배지 */}
                    {totalClips > 1 && (
                      <div style={{ position: 'absolute', bottom: '10px', right: '10px', backgroundColor: 'rgba(0,0,0,0.65)', color: '#e2e8f0', fontSize: '12px', fontWeight: '600', padding: '3px 8px', borderRadius: '12px' }}>
                        {curClipIdx + 1} / {totalClips}
                      </div>
                    )}
                  </div>

                  {/* 정보 영역 */}
                  <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', flex: 1 }}>
                    <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#fff', margin: '0 0 12px 0', lineHeight: '1.4' }}>{event.title}</h3>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#9ca3af', fontSize: '14px', marginBottom: '8px' }}>
                      <MapPin size={14} /> {event.location}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#9ca3af', fontSize: '14px', marginBottom: 'auto' }}>
                      <Clock size={14} /> {formatCctvTime(event.timestamp)}
                    </div>
                    <div style={{ display: 'flex', gap: '8px', marginTop: '20px', borderTop: '1px solid #334155', paddingTop: '20px', alignItems: 'center' }}>
                      <button
                        style={{ backgroundColor: hasClip ? '#60a5fa' : '#334155', color: hasClip ? '#0f172a' : '#6b7280', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px', cursor: hasClip ? 'pointer' : 'not-allowed', fontSize: '13px' }}
                        onClick={() => hasClip && setModalUrl(curClip.clip_url)}
                        disabled={!hasClip}
                      >
                        <Play size={14} /> 영상 보기
                      </button>
                      {/* 클립 네비게이션 */}
                      {totalClips > 1 && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginLeft: '8px' }}>
                          <button
                            onClick={(e) => goClip(-1, e)}
                            disabled={curClipIdx === 0}
                            style={{ background: 'none', border: '1px solid #334155', color: curClipIdx === 0 ? '#4b5563' : '#9ca3af', borderRadius: '4px', width: '28px', height: '28px', cursor: curClipIdx === 0 ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                          >
                            <ChevronLeft size={14} />
                          </button>
                          <span style={{ fontSize: '12px', color: '#9ca3af', minWidth: '48px', textAlign: 'center' }}>
                            클립 {curClipIdx + 1}/{totalClips}
                          </span>
                          <button
                            onClick={(e) => goClip(1, e)}
                            disabled={curClipIdx === totalClips - 1}
                            style={{ background: 'none', border: '1px solid #334155', color: curClipIdx === totalClips - 1 ? '#4b5563' : '#9ca3af', borderRadius: '4px', width: '28px', height: '28px', cursor: curClipIdx === totalClips - 1 ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                          >
                            <ChevronRight size={14} />
                          </button>
                        </div>
                      )}
                      {isAdmin && (
                        <button
                          title="이벤트 삭제"
                          style={{ marginLeft: 'auto', backgroundColor: 'rgba(239,68,68,0.1)', color: '#f87171', border: '1px solid rgba(239,68,68,0.25)', padding: '8px 14px', borderRadius: '6px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '13px' }}
                          onClick={() => handleDelete(event.id)}
                        >
                          <Trash2 size={14} /> 삭제
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
            {filteredEvents.length === 0 && !loading && (
              <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
                {rangeLabel()}에 해당하는 이벤트가 없습니다.
              </div>
            )}
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

export default EventHistory;
