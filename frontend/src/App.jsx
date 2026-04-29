import React, { useState, useEffect, useRef } from 'react';
import {
  Mic, Send, Plus, Search, Shield,
  Clock, Settings, User, MoreVertical, AlertCircle, X, Lock, LogIn, LogOut
} from 'lucide-react';

const App = () => {
  const [query, setQuery] = useState('');
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [loading, setLoading] = useState(false);

  // 로그인/로그아웃 관련 상태
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [user, setUser] = useState({ name: '방문객', role: 'Guest' });
  const [loginInput, setLoginInput] = useState({ id: '', pw: '' });

  const [recentSearches, setRecentSearches] = useState([
    { id: 1, title: '검은색 지갑', location: '3층 회의실', date: '2026-04-20', messages: [], user: '김지은님' },
    { id: 2, title: '애플 노트북', location: '카페테리아', date: '2026-04-19', messages: [], user: '박민수님' }
  ]);

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (currentSessionId && messages.length > 0) {
      setRecentSearches(prev => prev.map(s =>
        s.id === currentSessionId ? { ...s, messages: messages } : s
      ));
    }
  }, [messages, currentSessionId]);

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setQuery('');
  };

  const handleHistoryClick = (session) => {
    setCurrentSessionId(session.id);
    setMessages(session.messages || []);
    setQuery('');
  };

  const handleDeleteHistory = (e, id) => {
    e.stopPropagation();
    if (window.confirm('이 검색 기록을 삭제할까요?')) {
      setRecentSearches(prev => prev.filter(item => item.id !== id));
      if (currentSessionId === id) handleNewChat();
    }
  };

  const handleLogin = (e) => {
    e.preventDefault();
    if (loginInput.id && loginInput.pw) {
      setUser({ name: loginInput.id, role: 'Administrator' });
      setIsLoggedIn(true);
      setShowLoginModal(false);
      setLoginInput({ id: '', pw: '' });
    }
  };

  const executeLogout = () => {
    setIsLoggedIn(false);
    setUser({ name: '방문객', role: 'Guest' });
    setShowLogoutModal(false);
  };

  const startListening = () => {
    if (!('webkitSpeechRecognition' in window)) return;
    const recognition = new window.webkitSpeechRecognition();
    recognition.lang = 'ko-KR';
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setQuery(transcript);
      handleSearch(transcript);
    };
    recognition.start();
  };

  const handleSearch = async (text = query) => {
    if (!text || !text.trim()) return;
    let sessionId = currentSessionId;
    if (!sessionId) {
      sessionId = Date.now();
      setRecentSearches(prev => [{ id: sessionId, title: text, messages: [], location: '실시간 관제', date: new Date().toLocaleDateString(), user: user.name }, ...prev]);
      setCurrentSessionId(sessionId);
    }
    setMessages(prev => [...prev, { type: 'user', text }]);
    setQuery('');
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, top_k: 4 }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { type: 'ai', report: data.ai_report || data.answer || "보안 관련 질문을 입력해 주세요.", results: data.results || [], intent: data.intent_info?.intent || "OOD" }]);
    } catch (error) {
      setMessages(prev => [...prev, { type: 'ai', report: "서버 연결 오류가 발생했습니다.", intent: "ERROR" }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <button className="new-chat-btn" onClick={handleNewChat}><Plus size={18} /><span>새 채팅</span></button>
        <div className="search-box"><Search className="search-icon" size={14} /><input type="text" placeholder="분실물 검색..." /></div>
        <div className="history-section">
          <div className="history-title"><Clock size={12} /><span>최근 검색 기록</span></div>
          <div className="history-section-container" style={{ maxHeight: 'calc(100vh - 250px)', overflowY: 'auto' }}>
            {recentSearches.map(item => (
              <div key={item.id} className={`history-item group ${currentSessionId === item.id ? 'active' : ''}`} onClick={() => handleHistoryClick(item)} style={{ backgroundColor: currentSessionId === item.id ? '#1f2937' : 'transparent', position: 'relative', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ flex: 1, overflow: 'hidden' }}><div className="item-title" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: '20px' }}>{item.title}</div><div className="item-info">{item.location} • {item.date}</div></div>
                <X size={14} className="delete-btn" onClick={(e) => handleDeleteHistory(e, item.id)} style={{ color: '#6b7280', cursor: 'pointer', position: 'absolute', right: '10px', opacity: '0.4' }} />
              </div>
            ))}
          </div>
        </div>
        <div className="user-profile" onClick={isLoggedIn ? () => setShowLogoutModal(true) : () => setShowLoginModal(true)} style={{ cursor: 'pointer' }}>
          <div className="avatar" style={{ backgroundColor: isLoggedIn ? '#3b82f6' : '#6b7280' }}>{user.name[0]}</div>
          <div style={{ flex: 1 }}><div style={{ fontSize: '13px', fontWeight: '600' }}>{user.name}</div><div style={{ fontSize: '10px', color: '#6b7280' }}>{isLoggedIn ? user.role : '로그인 필요'}</div></div>
          {isLoggedIn ? <MoreVertical size={16} /> : <LogIn size={16} />}
        </div>
      </aside>

      <main className="main-content">
        <header className="header">
          <div className="header-logo">Searchlight <MoreVertical size={14} /></div>
          <div style={{ display: 'flex', gap: '20px', color: '#9ca3af' }}>
            <User size={18} cursor="pointer" onClick={isLoggedIn ? () => setShowLogoutModal(true) : () => setShowLoginModal(true)} style={{ color: isLoggedIn ? '#3b82f6' : '#9ca3af' }} />
            <Settings size={18} cursor="pointer" />
          </div>
        </header>

        <div className="chat-container" style={{ flex: 1, overflowY: 'auto', padding: '40px' }}>
          {messages.length === 0 ? (
            <div className="welcome-screen" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <h1 className="welcome-title" style={{ fontSize: '28px', textAlign: 'center', lineHeight: '1.5', fontWeight: '300' }}>Searchlight AI가 실시간 감시 중입니다.<br />분석이 필요한 내용을 입력하세요.</h1>
            </div>
          ) : (
            <div style={{ maxWidth: '800px', margin: '0 auto' }}>
              {messages.map((msg, i) => (
                <div key={i} style={{ marginBottom: '30px', display: 'flex', flexDirection: 'column', alignItems: msg.type === 'user' ? 'flex-end' : 'flex-start' }}>
                  {msg.type === 'user' ? (
                    <div style={{ backgroundColor: '#3b82f6', padding: '12px 20px', borderRadius: '15px 15px 0 15px', maxWidth: '80%', fontSize: '14px' }}>{msg.text}</div>
                  ) : (
                    <div style={{ width: '100%', backgroundColor: msg.intent === 'ERROR' ? '#450a0a' : '#1a2235', padding: '25px', borderRadius: '15px', border: msg.intent === 'ERROR' ? '1px solid #ef4444' : '1px solid rgba(255,255,255,0.1)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px', color: msg.intent === 'ERROR' ? '#f87171' : '#3b82f6', fontSize: '13px', fontWeight: 'bold' }}>{msg.intent === 'ERROR' ? <AlertCircle size={16} /> : <Shield size={16} />} {msg.intent === 'ERROR' ? "시스템 오류" : "AI 분석 보고서"}<span style={{ flex: 1 }}></span><span style={{ fontSize: '10px', color: '#6b7280' }}>{msg.intent}</span></div>
                      <p style={{ fontSize: '14px', lineHeight: '1.6', color: '#d1d5db' }}>{msg.report}</p>
                      {msg.results?.length > 0 && (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '15px', marginTop: '20px' }}>
                          {msg.results.map((res, j) => (
                            <div key={j} style={{ backgroundColor: '#0b0f19', borderRadius: '10px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.05)' }}>
                              <video src={`http://localhost:8000${res.video_url}`} style={{ width: '100%', height: '120px', objectFit: 'cover' }} controls preload="metadata" /><div style={{ padding: '10px' }}><div style={{ fontSize: '10px', color: '#3b82f6', display: 'flex', justifyContent: 'space-between' }}><span>{res.timestamp}</span><span>{(res.score * 100).toFixed(0)}%</span></div><div style={{ fontSize: '11px', color: '#9ca3af', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{res.description}</div></div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
              {loading && <div style={{ color: '#3b82f6', fontSize: '12px', fontStyle: 'italic' }}>AI 분석 중...</div>}<div ref={chatEndRef} />
            </div>
          )}
        </div>

        <div className="input-area"><div className="input-container" style={{ padding: '20px 40px 40px' }}><div className="input-wrapper">
          <Plus size={20} style={{ color: '#6b7280', cursor: 'pointer' }} /><input type="text" placeholder="질문을 입력하세요..." value={query} onChange={(e) => setQuery(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSearch()} /><Mic size={20} className="icon-btn" onClick={startListening} style={{ color: isListening ? '#3b82f6' : '#6b7280' }} /><button className="icon-btn send-btn" onClick={() => handleSearch()} style={{ marginLeft: '10px' }}><Send size={18} /></button>
        </div></div></div>
      </main>

      {/* Login Modal */}
      {showLoginModal && (
        <div className="modal-overlay" style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(5px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="modal-content" style={{ backgroundColor: '#111827', padding: '40px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)', width: '350px' }}>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}><div style={{ padding: '15px', backgroundColor: '#3b82f6', borderRadius: '15px' }}><Lock size={32} /></div></div>
            <h2 style={{ textAlign: 'center', marginBottom: '10px', fontSize: '20px' }}>시스템 관리자 인증</h2>
            <p style={{ textAlign: 'center', color: '#6b7280', fontSize: '12px', marginBottom: '30px' }}>계정 정보를 입력해 주세요.</p>
            <form onSubmit={handleLogin}>
              <div style={{ marginBottom: '15px' }}><label style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '5px', display: 'block' }}>ID</label><input type="text" required value={loginInput.id} onChange={(e) => setLoginInput({ ...loginInput, id: e.target.value })} style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '12px', color: 'white' }} placeholder="관리자 아이디" /></div>
              <div style={{ marginBottom: '30px' }}><label style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '5px', display: 'block' }}>PASSWORD</label><input type="password" required value={loginInput.pw} onChange={(e) => setLoginInput({ ...loginInput, pw: e.target.value })} style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '12px', color: 'white' }} placeholder="••••••••" /></div>
              <button type="submit" style={{ width: '100%', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '10px', padding: '14px', fontWeight: 'bold', cursor: 'pointer' }}>인증 및 로그인</button>
              <button type="button" onClick={() => setShowLoginModal(false)} style={{ width: '100%', background: 'transparent', color: '#6b7280', border: 'none', marginTop: '15px', fontSize: '12px', cursor: 'pointer' }}>닫기</button>
            </form>
          </div>
        </div>
      )}

      {/* Logout Confirmation Modal */}
      {showLogoutModal && (
        <div className="modal-overlay" style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(5px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div className="modal-content" style={{ backgroundColor: '#111827', padding: '40px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)', width: '350px', textAlign: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}><div style={{ padding: '15px', backgroundColor: '#ef4444', borderRadius: '15px' }}><LogOut size={32} /></div></div>
            <h2 style={{ marginBottom: '10px', fontSize: '20px' }}>로그아웃</h2>
            <p style={{ color: '#6b7280', fontSize: '12px', marginBottom: '30px' }}>정말 시스템에서 로그아웃 하시겠습니까?</p>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={executeLogout} style={{ flex: 1, backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '10px', padding: '14px', fontWeight: 'bold', cursor: 'pointer' }}>로그아웃</button>
              <button onClick={() => setShowLogoutModal(false)} style={{ flex: 1, backgroundColor: '#1f2937', color: 'white', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', padding: '14px', fontWeight: 'bold', cursor: 'pointer' }}>취소</button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .chat-container::-webkit-scrollbar { width: 6px; }
        .chat-container::-webkit-scrollbar-track { background: transparent; }
        .chat-container::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
        .history-section-container::-webkit-scrollbar { display: none; }
        .history-section-container { -ms-overflow-style: none; scrollbar-width: none; }
        .history-item.active { border-left: 3px solid #3b82f6; }
        .delete-btn:hover { color: #ef4444 !important; opacity: 1 !important; transform: scale(1.2); transition: all 0.2s; }
      `}</style>
    </div>
  );
};

export default App;