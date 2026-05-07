import React, { useState, useEffect } from 'react';
import { Search, Calendar, Filter, Download, Play, Share2, MapPin, Clock, User, Car } from 'lucide-react';

const EventHistory = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const [filterTime, setFilterTime] = useState(() => new Date().toISOString().split('T')[0]);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/alerts/events?limit=300');
      if (response.ok) {
        const data = await response.json();
        setEvents(data);
      }
    } catch (error) {
      console.error('Failed to fetch events:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredEvents = events.filter(e => {
    const matchesSearch = e.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          e.location.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (!matchesSearch) return false;

    if (filterTime !== 'all') {
      const formattedEventDate = e.timestamp ? e.timestamp.split('T')[0].split(' ')[0] : '';
      return formattedEventDate === filterTime;
    }
    
    return true;
  });

  const handleDownload = () => {
    if (filteredEvents.length === 0) {
      alert("다운로드할 이벤트가 없습니다.");
      return;
    }

    const headers = ["ID", "이벤트 내용", "위치", "발생 시각", "대상", "신뢰도(%)"];
    
    const csvRows = filteredEvents.map(e => {
      const targetLabel = e.tag === 'Person' ? '사람' : e.tag === 'Vehicle' ? '차량' : (e.tag || '이벤트');
      return [
        e.id || '',
        `"${(e.title || '').replace(/"/g, '""')}"`,
        `"${e.location || ''}"`,
        `"${e.timestamp || ''}"`,
        targetLabel,
        e.confidence || ''
      ].join(',');
    });

    const csvContent = "\uFEFF" + headers.join(',') + "\n" + csvRows.join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `보안이벤트_보고서_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ padding: '30px 40px', maxWidth: '1200px', margin: '0 auto', width: '100%', color: '#f3f4f6' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: '0 0 8px 0', color: '#fff' }}>영상 보관함</h1>
          <p style={{ color: '#9ca3af', margin: 0, fontSize: '14px' }}>감지된 모든 보안 이벤트 영상을 조회하고 검색합니다.</p>
        </div>
        <button style={{ backgroundColor: '#60a5fa', color: '#0f172a', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px' }} onClick={handleDownload}>
          <Download size={16} /> 다운로드
        </button>
      </div>

      <div style={{ display: 'flex', gap: '16px', marginBottom: '32px' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: '#6b7280' }} />
          <input 
            type="text" 
            placeholder="상황 설명, 위치 또는 카메라 이름으로 검색..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ width: '100%', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', padding: '12px 16px 12px 42px', color: '#fff', fontSize: '14px', outline: 'none' }}
          />
        </div>
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          <input 
            type="date"
            value={filterTime !== 'all' ? filterTime : ''}
            onChange={(e) => setFilterTime(e.target.value || 'all')}
            style={{ 
              backgroundColor: filterTime !== 'all' ? 'rgba(59, 130, 246, 0.2)' : '#1e293b', 
              border: filterTime !== 'all' ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid #334155', 
              color: filterTime !== 'all' ? '#60a5fa' : '#9ca3af', 
              padding: '12px 16px', borderRadius: '8px', cursor: 'pointer', fontFamily: 'inherit', outline: 'none', height: '100%',
              colorScheme: 'dark'
            }}
          />
        </div>
        <button 
          onClick={() => setFilterTime('all')}
          style={{ 
            backgroundColor: filterTime === 'all' ? 'rgba(59, 130, 246, 0.2)' : '#1e293b', 
            border: filterTime === 'all' ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid #334155', 
            color: filterTime === 'all' ? '#60a5fa' : '#fff', 
            padding: '0 16px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' 
          }}
        >
          <Filter size={16} color={filterTime === 'all' ? '#60a5fa' : '#9ca3af'} /> 모든 이벤트
        </button>
      </div>

      <div style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '16px', paddingBottom: '16px', borderBottom: '1px solid #1e293b' }}>
        총 {filteredEvents.length}개의 이벤트
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>이벤트를 불러오는 중입니다...</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {filteredEvents.map((event, idx) => (
            <div key={idx} style={{ backgroundColor: '#1e293b', borderRadius: '12px', overflow: 'hidden', display: 'flex', flexDirection: 'row', border: '1px solid #334155' }}>
              {/* Thumbnail */}
              <div style={{ width: '280px', height: '200px', position: 'relative', flexShrink: 0 }}>
                <img 
                  src={`http://localhost:8000${event.image_path}`} 
                  alt="이벤트 썸네일" 
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  onError={(e) => { e.target.src = 'https://via.placeholder.com/280x200?text=No+Image' }}
                />
                
                {/* Tag */}
                <div style={{ position: 'absolute', top: '12px', left: '12px', backgroundColor: 'rgba(0,0,0,0.6)', padding: '4px 10px', borderRadius: '20px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: '500', backdropFilter: 'blur(4px)', color: event.tag.includes('Person') ? '#60a5fa' : '#fbbf24' }}>
                  {event.tag.includes('Person') ? <User size={12} /> : <Car size={12} />}
                  {event.tag === 'Person' ? '사람' : event.tag === 'Vehicle' ? '차량' : event.tag || '이벤트'}
                </div>
                
                {/* Confidence */}
                <div style={{ position: 'absolute', top: '12px', right: '12px', backgroundColor: 'rgba(0,0,0,0.6)', padding: '4px 8px', borderRadius: '20px', fontSize: '12px', fontWeight: '600', backdropFilter: 'blur(4px)', color: '#fff' }}>
                  {event.confidence}%
                </div>
              </div>

              {/* Content */}
              <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#fff', margin: '0 0 12px 0' }}>{event.title}</h3>
                  <span style={{ fontSize: '12px', color: '#6b7280' }}>CAM-00{Math.floor(Math.random() * 5) + 1}</span>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#9ca3af', fontSize: '14px', marginBottom: '8px' }}>
                  <MapPin size={14} /> {event.location}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#9ca3af', fontSize: '14px', marginBottom: 'auto' }}>
                  <Clock size={14} /> {event.timestamp ? new Date(event.timestamp).toLocaleString('ko-KR') : ''}
                </div>
                
                {/* Actions */}
                <div style={{ display: 'flex', gap: '16px', marginTop: '20px', borderTop: '1px solid #334155', paddingTop: '20px' }}>
                  <button style={{ backgroundColor: '#60a5fa', color: '#0f172a', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px' }} onClick={() => alert('영상 보기 연동 준비 중')}>
                    <Play size={14} /> 영상 보기
                  </button>
                  <button style={{ backgroundColor: 'transparent', color: '#e2e8f0', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: '500', cursor: 'pointer', fontSize: '13px' }} onClick={() => alert('다운로드 기능 준비 중')}>
                    다운로드
                  </button>
                  <button style={{ backgroundColor: 'transparent', color: '#e2e8f0', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: '500', cursor: 'pointer', fontSize: '13px' }} onClick={() => alert('공유 기능 준비 중')}>
                    공유하기
                  </button>
                </div>
              </div>
            </div>
          ))}
          {filteredEvents.length === 0 && !loading && (
            <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>이벤트를 찾을 수 없습니다.</div>
          )}
        </div>
      )}
    </div>
  );
};

export default EventHistory;
