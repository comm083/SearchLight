import React, { useState } from 'react';
import { Shield, AlertCircle, ThumbsDown, X, Check } from 'lucide-react';

const SITUATION_COLORS = {
  assault: { bg: 'rgba(239,68,68,0.15)', color: '#f87171', label: '폭행' },
  theft:   { bg: 'rgba(251,146,60,0.15)', color: '#fb923c', label: '절도' },
  falling: { bg: 'rgba(250,204,21,0.15)', color: '#facc15', label: '낙상' },
  break:   { bg: 'rgba(167,139,250,0.15)', color: '#a78bfa', label: '기물파손' },
  smoking: { bg: 'rgba(59,130,246,0.15)', color: '#60a5fa', label: '흡연' },
  disaster:{ bg: 'rgba(239,68,68,0.15)', color: '#f87171', label: '재난' },
};

const formatTs = (ts) => {
  if (!ts) return '';
  const d = new Date(ts);
  if (isNaN(d.getTime())) return ts;
  const h = d.getUTCHours();
  const mi = String(d.getUTCMinutes()).padStart(2, '0');
  const s = String(d.getUTCSeconds()).padStart(2, '0');
  const ampm = h < 12 ? '오전' : '오후';
  const h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
  return `${d.getUTCFullYear()}. ${d.getUTCMonth() + 1}. ${d.getUTCDate()}. ${ampm} ${h12}:${mi}:${s}`;
};

const parseKoreanDate = (q) => {
  // "2025년 5월 16일", "5월 16일", "5/16", "05-16" 등 파싱
  let year = null, month = null, day = null;
  let m;
  m = q.match(/(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일/);
  if (m) { year = +m[1]; month = +m[2]; day = +m[3]; }
  else {
    m = q.match(/(\d{1,2})월\s*(\d{1,2})일/);
    if (m) { month = +m[1]; day = +m[2]; }
    else {
      m = q.match(/^(\d{1,2})\/(\d{1,2})$/);
      if (m) { month = +m[1]; day = +m[2]; }
    }
  }
  if (!month || !day) return null;
  return { year, month, day };
};

const SITUATION_FILTER_OPTIONS = [
  { key: null, label: '전체' },
  { key: 'assault', label: '폭행' },
  { key: 'theft', label: '절도' },
  { key: 'falling', label: '낙상' },
  { key: 'break', label: '기물파손' },
  { key: 'smoking', label: '흡연' },
];

const MessageItem = ({ msg, expandedResults, setExpandedResults, index, sessionId }) => {
  const isUser = msg.type === 'user';
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [showPanel, setShowPanel] = useState(false);
  const [comment, setComment] = useState('');
  const [events, setEvents] = useState([]);
  const [selectedEventId, setSelectedEventId] = useState(null);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [eventSearch, setEventSearch] = useState('');
  const [sitFilter, setSitFilter] = useState(null);
  const [dateFilter, setDateFilter] = useState('');

  const openPanel = async () => {
    if (feedbackSent || showPanel) return;
    setShowPanel(true);
    setLoadingEvents(true);
    try {
      const res = await fetch('http://localhost:8000/api/alerts/events?limit=50');
      if (res.ok) setEvents(await res.json());
    } catch (e) {
      console.error('events fetch error', e);
    } finally {
      setLoadingEvents(false);
    }
  };

  const handleSubmit = async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/history/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          feedback_type: 'wrong_result',
          comment: JSON.stringify({
            comment: comment.trim() || null,
            correct_event_id: selectedEventId || null,
          }),
        }),
      });
      if (res.ok) {
        setFeedbackSent(true);
        setShowPanel(false);
      }
    } catch (e) {
      console.error('Feedback error:', e);
    } finally {
      setSubmitting(false);
    }
  };

  if (isUser) {
    return (
      <div style={{ marginBottom: '30px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
        <div style={{ backgroundColor: '#3b82f6', padding: '12px 20px', borderRadius: '15px 15px 0 15px', maxWidth: '80%', fontSize: '14px' }}>
          {msg.text}
        </div>
      </div>
    );
  }

  const isError = msg.intent === 'ERROR';

  return (
    <div style={{ marginBottom: '30px', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', width: '100%' }}>
      <div style={{
        width: '100%',
        backgroundColor: isError ? '#450a0a' : '#1a2235',
        padding: '25px',
        borderRadius: '15px',
        border: isError ? '1px solid #ef4444' : '1px solid rgba(255,255,255,0.1)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px', color: isError ? '#f87171' : '#3b82f6', fontSize: '13px', fontWeight: 'bold' }}>
          {isError ? <AlertCircle size={16} /> : <Shield size={16} />}
          {isError ? '시스템 오류' : 'AI 분석 보고서'}
          <span style={{ flex: 1 }} />
          <span style={{ fontSize: '10px', color: '#6b7280' }}>{msg.intent}</span>
        </div>

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

        {/* 피드백 버튼 */}
        {msg.intent !== 'CHITCHAT' && msg.intent !== 'ERROR' && (
          <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'flex-end' }}>
            {feedbackSent ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10b981', fontSize: '11px' }}>
                <Check size={12} /> 피드백이 접수되었습니다. 감사합니다.
              </div>
            ) : (
              <button
                onClick={openPanel}
                style={{
                  display: 'flex', alignItems: 'center', gap: '6px',
                  background: showPanel ? 'rgba(239,68,68,0.2)' : 'rgba(239,68,68,0.1)',
                  color: '#ef4444',
                  border: '1px solid rgba(239,68,68,0.2)',
                  padding: '6px 12px', borderRadius: '6px', fontSize: '11px', cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                <ThumbsDown size={12} /> 잘못된 결과 (피드백)
              </button>
            )}
          </div>
        )}

        {/* 피드백 패널 */}
        {showPanel && (
          <div style={{ marginTop: '16px', backgroundColor: '#0f172a', borderRadius: '10px', border: '1px solid rgba(239,68,68,0.2)', padding: '20px' }}>
            {/* 헤더 */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <span style={{ fontSize: '13px', fontWeight: '600', color: '#f3f4f6' }}>피드백 제출</span>
              <button
                onClick={() => setShowPanel(false)}
                style={{ background: 'none', border: 'none', color: '#6b7280', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
              >
                <X size={16} />
              </button>
            </div>

            {/* A: 코멘트 입력 */}
            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '12px', color: '#9ca3af', display: 'block', marginBottom: '6px' }}>
                어떤 점이 잘못됐나요? <span style={{ color: '#4b5563' }}>(선택)</span>
              </label>
              <textarea
                value={comment}
                onChange={e => setComment(e.target.value)}
                placeholder="예: 시간이 다릅니다 / 영상이 다릅니다 / 상황 분류가 틀렸습니다"
                rows={2}
                style={{
                  width: '100%', boxSizing: 'border-box',
                  backgroundColor: '#1e293b', border: '1px solid #334155',
                  borderRadius: '6px', color: '#f3f4f6', fontSize: '13px',
                  padding: '10px 12px', resize: 'vertical', outline: 'none',
                  fontFamily: 'inherit',
                }}
              />
            </div>

            {/* C: 올바른 영상 선택 */}
            <div>
              <label style={{ fontSize: '12px', color: '#9ca3af', display: 'block', marginBottom: '8px' }}>
                어떤 영상이 잘못되었나요? <span style={{ color: '#4b5563' }}>(선택)</span>
              </label>

              {/* 상황 유형 필터 */}
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '8px' }}>
                {SITUATION_FILTER_OPTIONS.map(opt => (
                  <button
                    key={String(opt.key)}
                    onClick={() => setSitFilter(opt.key)}
                    style={{
                      padding: '3px 10px', borderRadius: '12px', border: 'none', cursor: 'pointer',
                      fontSize: '11px', fontWeight: '600',
                      backgroundColor: sitFilter === opt.key ? '#3b82f6' : '#1e293b',
                      color: sitFilter === opt.key ? '#fff' : '#6b7280',
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>

              {/* 날짜 + 텍스트 검색 */}
              <div style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
                <input
                  type="date"
                  value={dateFilter}
                  onChange={e => setDateFilter(e.target.value)}
                  style={{
                    flex: '0 0 auto',
                    backgroundColor: '#1e293b', border: '1px solid #334155',
                    borderRadius: '6px', color: dateFilter ? '#f3f4f6' : '#6b7280', fontSize: '12px',
                    padding: '7px 10px', outline: 'none', fontFamily: 'inherit', colorScheme: 'dark',
                  }}
                />
                <input
                  type="text"
                  value={eventSearch}
                  onChange={e => setEventSearch(e.target.value)}
                  placeholder="영상 요약, 파일명으로 검색..."
                  style={{
                    flex: 1, boxSizing: 'border-box',
                    backgroundColor: '#1e293b', border: '1px solid #334155',
                    borderRadius: '6px', color: '#f3f4f6', fontSize: '12px',
                    padding: '7px 10px', outline: 'none', fontFamily: 'inherit',
                  }}
                />
              </div>

              {(() => {
                if (loadingEvents) return <div style={{ color: '#4b5563', fontSize: '12px', padding: '12px 0' }}>영상 목록 불러오는 중...</div>;
                if (events.length === 0) return <div style={{ color: '#4b5563', fontSize: '12px', padding: '12px 0' }}>영상 목록이 없습니다.</div>;
                const parsedDate = parseKoreanDate(eventSearch.trim());
                const filtered = events.filter(ev => {
                  const matchSit = sitFilter === null || ev.tag === sitFilter;
                  const q = eventSearch.trim().toLowerCase();

                  let matchText = true;
                  let matchDate = true;

                  if (parsedDate) {
                    // 한국어 날짜 표현이면 날짜 필터로 처리
                    if (ev.timestamp) {
                      const evDate = new Date(ev.timestamp);
                      const evY = evDate.getUTCFullYear();
                      const evM = evDate.getUTCMonth() + 1;
                      const evD = evDate.getUTCDate();
                      matchDate = evM === parsedDate.month && evD === parsedDate.day
                        && (parsedDate.year === null || evY === parsedDate.year);
                    } else {
                      matchDate = false;
                    }
                  } else if (q) {
                    matchText = (ev.short_summary || '').toLowerCase().includes(q)
                      || (ev.location || '').toLowerCase().includes(q);
                  }

                  // date picker 필터
                  if (dateFilter && ev.timestamp && !parsedDate) {
                    const evDate = new Date(ev.timestamp);
                    const y = evDate.getUTCFullYear();
                    const m = String(evDate.getUTCMonth() + 1).padStart(2, '0');
                    const d = String(evDate.getUTCDate()).padStart(2, '0');
                    matchDate = `${y}-${m}-${d}` === dateFilter;
                  }

                  return matchSit && matchText && matchDate;
                });
                if (filtered.length === 0) return <div style={{ color: '#4b5563', fontSize: '12px', padding: '12px 0' }}>검색 결과가 없습니다.</div>;
                return (
                  <div style={{ maxHeight: '240px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px', paddingRight: '4px' }}>
                    {filtered.map(ev => {
                      const sit = ev.tag && ev.tag !== 'normal' ? SITUATION_COLORS[ev.tag] : null;
                      const isSelected = selectedEventId === ev.id;
                      return (
                        <div
                          key={ev.id}
                          onClick={() => setSelectedEventId(isSelected ? null : ev.id)}
                          style={{
                            display: 'flex', alignItems: 'center', gap: '10px',
                            padding: '8px 12px', borderRadius: '8px', cursor: 'pointer',
                            backgroundColor: isSelected ? 'rgba(59,130,246,0.15)' : '#1e293b',
                            border: isSelected ? '1px solid rgba(59,130,246,0.4)' : '1px solid #334155',
                            transition: 'all 0.15s',
                          }}
                        >
                          <div style={{
                            width: '16px', height: '16px', borderRadius: '50%', flexShrink: 0,
                            backgroundColor: isSelected ? '#3b82f6' : 'transparent',
                            border: isSelected ? '2px solid #3b82f6' : '2px solid #334155',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                          }}>
                            {isSelected && <Check size={10} color="#fff" />}
                          </div>
                          {sit && (
                            <span style={{ fontSize: '10px', padding: '2px 7px', borderRadius: '10px', backgroundColor: sit.bg, color: sit.color, fontWeight: '700', flexShrink: 0 }}>
                              {sit.label}
                            </span>
                          )}
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontSize: '11px', color: '#60a5fa', marginBottom: '2px' }}>{formatTs(ev.timestamp)}</div>
                            <div style={{ fontSize: '12px', color: '#cbd5e1', overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
                              {ev.short_summary || ev.title || ev.location}
                            </div>
                          </div>
                          <div style={{ fontSize: '10px', color: '#4b5563', flexShrink: 0 }}>{ev.location}</div>
                        </div>
                      );
                    })}
                  </div>
                );
              })()}
            </div>

            {/* 제출 버튼 */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '16px' }}>
              <button
                onClick={() => setShowPanel(false)}
                style={{ padding: '7px 16px', borderRadius: '6px', border: '1px solid #334155', background: 'none', color: '#9ca3af', fontSize: '12px', cursor: 'pointer' }}
              >
                취소
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting || (!comment.trim() && !selectedEventId)}
                style={{
                  padding: '7px 16px', borderRadius: '6px', border: 'none',
                  backgroundColor: (!comment.trim() && !selectedEventId) ? '#1e293b' : '#3b82f6',
                  color: (!comment.trim() && !selectedEventId) ? '#4b5563' : '#fff',
                  fontSize: '12px', fontWeight: '600',
                  cursor: (!comment.trim() && !selectedEventId) ? 'not-allowed' : 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                {submitting ? '제출 중...' : '제출'}
              </button>
            </div>
          </div>
        )}

        {/* Results */}
        {msg.results?.length > 0 && (
          <div style={{ marginTop: '20px' }}>
            <div style={{ color: '#9ca3af', fontSize: '12px', marginBottom: '10px' }}>검색 결과 {msg.results.length}건</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageItem;
