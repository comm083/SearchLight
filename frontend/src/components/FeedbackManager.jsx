import React, { useState, useEffect, useCallback } from 'react';
import { CheckCircle, Zap, Clock, MessageSquare, RefreshCw } from 'lucide-react';

const SITUATION_LABELS = {
  assault: { label: '폭행', color: '#f87171', bg: 'rgba(239,68,68,0.15)' },
  theft:   { label: '절도', color: '#fb923c', bg: 'rgba(251,146,60,0.15)' },
  falling: { label: '낙상', color: '#facc15', bg: 'rgba(250,204,21,0.15)' },
  break:   { label: '기물파손', color: '#a78bfa', bg: 'rgba(167,139,250,0.15)' },
  smoking: { label: '흡연', color: '#60a5fa', bg: 'rgba(59,130,246,0.15)' },
  disaster:{ label: '재난', color: '#f87171', bg: 'rgba(239,68,68,0.15)' },
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

const FeedbackManager = () => {
  const [feedbacks, setFeedbacks] = useState([]);
  const [filter, setFilter] = useState('pending');
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);

  const fetchFeedbacks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/history/feedbacks?status=${filter}`);
      if (res.ok) setFeedbacks(await res.json());
    } catch (e) {
      console.error('피드백 조회 실패', e);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { fetchFeedbacks(); }, [fetchFeedbacks]);

  const handleResolve = async (id) => {
    setProcessingId(id);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/history/feedback/${id}/resolve`, { method: 'POST' });
      if (res.ok) fetchFeedbacks();
    } finally {
      setProcessingId(null);
    }
  };

  const handleBoost = async (id) => {
    setProcessingId(id);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/history/feedback/${id}/boost`, { method: 'POST' });
      const data = await res.json();
      alert(data.message);
      if (data.status === 'success') fetchFeedbacks();
    } finally {
      setProcessingId(null);
    }
  };

  const pendingCount = feedbacks.filter(f => f.feedback === 'wrong_result').length;

  return (
    <div style={{ padding: '30px 40px', maxWidth: '1000px', margin: '0 auto', color: '#f3f4f6' }}>
      {/* 헤더 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: '0 0 8px 0', color: '#fff' }}>피드백 관리</h1>
          <p style={{ color: '#9ca3af', margin: 0, fontSize: '14px' }}>
            사용자가 제출한 오답 피드백을 검토하고 검색 품질을 개선합니다.
          </p>
        </div>
        <button
          onClick={fetchFeedbacks}
          style={{ background: 'none', border: '1px solid #334155', color: '#9ca3af', borderRadius: '8px', padding: '8px 14px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}
        >
          <RefreshCw size={14} /> 새로고침
        </button>
      </div>

      {/* 필터 탭 */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
        {[
          { key: 'pending', label: `미처리 ${pendingCount > 0 ? `(${pendingCount})` : ''}` },
          { key: 'resolved', label: '처리 완료' },
          { key: 'all', label: '전체' },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            style={{
              padding: '6px 16px', borderRadius: '6px', border: 'none', cursor: 'pointer',
              fontSize: '13px', fontWeight: '600',
              backgroundColor: filter === key ? '#3b82f6' : '#1e293b',
              color: filter === key ? '#fff' : '#9ca3af',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* 목록 */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#4b5563' }}>불러오는 중...</div>
      ) : feedbacks.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px', color: '#4b5563' }}>
          {filter === 'pending' ? '미처리 피드백이 없습니다.' : '피드백이 없습니다.'}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {feedbacks.map((fb) => {
            const comment = fb.parsed_comment?.comment;
            const correctEvent = fb.correct_event;
            const isResolved = fb.feedback === 'resolved';
            const isProcessing = processingId === fb.id;
            const sit = correctEvent?.situation ? SITUATION_LABELS[correctEvent.situation] : null;

            return (
              <div
                key={fb.id}
                style={{
                  backgroundColor: '#1e293b',
                  borderRadius: '12px',
                  border: `1px solid ${isResolved ? '#1e3a2f' : 'rgba(239,68,68,0.2)'}`,
                  overflow: 'hidden',
                }}
              >
                {/* 상태 바 */}
                <div style={{
                  height: '3px',
                  backgroundColor: isResolved ? '#10b981' : '#ef4444',
                }} />

                <div style={{ padding: '20px 24px' }}>
                  {/* 상단: 질문 + 시각 + 상태 */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px', gap: '12px' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={11} /> {new Date(fb.created_at).toLocaleString('ko-KR')}
                      </div>
                      <div style={{ fontSize: '15px', fontWeight: '600', color: '#f3f4f6' }}>
                        "{fb.query}"
                      </div>
                    </div>
                    <span style={{
                      fontSize: '11px', padding: '3px 10px', borderRadius: '20px', fontWeight: '700', flexShrink: 0,
                      backgroundColor: isResolved ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                      color: isResolved ? '#10b981' : '#f87171',
                    }}>
                      {isResolved ? '처리 완료' : '미처리'}
                    </span>
                  </div>

                  <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                    {/* A: 코멘트 */}
                    {comment && (
                      <div style={{ flex: 1, minWidth: '200px', backgroundColor: '#0f172a', borderRadius: '8px', padding: '12px 16px', border: '1px solid #334155' }}>
                        <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <MessageSquare size={11} /> 사용자 코멘트
                        </div>
                        <div style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: '1.5' }}>{comment}</div>
                      </div>
                    )}

                    {/* C: 정답 영상 */}
                    {correctEvent ? (
                      <div style={{ flex: 1, minWidth: '200px', backgroundColor: '#0f172a', borderRadius: '8px', padding: '12px 16px', border: '1px solid #334155' }}>
                        <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '6px' }}>선택된 정답 영상</div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                          {sit && (
                            <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', backgroundColor: sit.bg, color: sit.color, fontWeight: '700' }}>
                              {sit.label}
                            </span>
                          )}
                          <span style={{ fontSize: '12px', color: '#60a5fa' }}>{formatTs(correctEvent.timestamp)}</span>
                        </div>
                        <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                          {correctEvent.short_summary || correctEvent.video_filename}
                        </div>
                      </div>
                    ) : (
                      !comment && (
                        <div style={{ flex: 1, minWidth: '200px', backgroundColor: '#0f172a', borderRadius: '8px', padding: '12px 16px', border: '1px solid #334155', color: '#4b5563', fontSize: '13px' }}>
                          코멘트 또는 정답 영상 없음
                        </div>
                      )
                    )}
                  </div>

                  {/* 액션 버튼 */}
                  {!isResolved && (
                    <div style={{ display: 'flex', gap: '8px', marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #334155' }}>
                      <button
                        onClick={() => handleResolve(fb.id)}
                        disabled={isProcessing}
                        style={{
                          display: 'flex', alignItems: 'center', gap: '6px',
                          padding: '7px 14px', borderRadius: '6px', border: '1px solid #334155',
                          backgroundColor: '#1e293b', color: '#9ca3af',
                          fontSize: '12px', cursor: 'pointer', fontWeight: '600',
                        }}
                      >
                        <CheckCircle size={13} /> 처리 완료
                      </button>
                      {correctEvent && (
                        <button
                          onClick={() => handleBoost(fb.id)}
                          disabled={isProcessing}
                          style={{
                            display: 'flex', alignItems: 'center', gap: '6px',
                            padding: '7px 14px', borderRadius: '6px', border: 'none',
                            backgroundColor: '#3b82f6', color: '#fff',
                            fontSize: '12px', cursor: 'pointer', fontWeight: '600',
                          }}
                        >
                          <Zap size={13} /> 품질 개선 적용
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 안내 */}
      <div style={{ marginTop: '32px', padding: '16px 20px', backgroundColor: '#0f172a', borderRadius: '10px', border: '1px solid #1e293b', fontSize: '13px', color: '#6b7280', lineHeight: '1.8' }}>
        <strong style={{ color: '#9ca3af' }}>품질 개선 적용이란?</strong><br />
        사용자가 선택한 정답 영상의 검색 데이터에 해당 질문 텍스트를 추가합니다.<br />
        이후 동일하거나 유사한 질문이 들어올 때 해당 영상이 상위에 노출됩니다.
      </div>
    </div>
  );
};

export default FeedbackManager;
