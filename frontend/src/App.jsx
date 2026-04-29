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
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [loading, setLoading] = useState(false);
  const [expandedResults, setExpandedResults] = useState({}); // 확장된 카드 상태 관리
  
  // 로그인/로그아웃 관련 상태
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [user, setUser] = useState({ name: '방문객', role: 'Guest' });
  const [loginInput, setLoginInput] = useState({ id: '', pw: '' });

  const [recentSearches, setRecentSearches] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  
  // 설정 관련 상태
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [settings, setSettings] = useState({
    sensitivity: 70,
    enableSound: true,
    viewMode: 'list', // 'list' 또는 'map'
    autoDeleteDays: 30
  });

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 백엔드에서 검색 기록 가져오기
  const fetchHistory = async () => {
    try {
      const sessionId = isLoggedIn ? user.name : 'guest';
      const res = await fetch(`http://localhost:8000/api/history/${sessionId}`);
      const data = await res.json();
      if (data.status === 'success' && data.history) {
        const formattedHistory = data.history.map(item => ({
          id: item.id,
          title: item.query,
          location: item.intent,
          date: new Date(item.created_at).toLocaleDateString(),
          ai_report: item.ai_report,
          messages: [
            { type: 'user', text: item.query },
            { type: 'ai', report: item.ai_report, intent: item.intent }
          ]
        }));
        setRecentSearches(formattedHistory);
      }
    } catch (error) {
      console.error("히스토리 로딩 실패:", error);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [isLoggedIn, user.name]);

  useEffect(() => {
    if (currentSessionId && messages.length > 0) {
      // 로컬 상태 업데이트 (실시간 반영용)
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
    // 히스토리 항목 클릭 시 해당 메시지 복구
    if (session.messages && session.messages.length > 0) {
      setMessages(session.messages);
    } else if (session.ai_report) {
      setMessages([
        { type: 'user', text: session.title },
        { type: 'ai', report: session.ai_report, intent: session.location }
      ]);
    } else {
      setMessages([]);
    }
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

  // STT (음성 인식) 함수
  const startListening = () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert("이 브라우저는 음성 인식을 지원하지 않습니다.");
      return;
    }
    const recognition = new window.webkitSpeechRecognition();
    recognition.lang = 'ko-KR';
    recognition.interimResults = false;
    recognition.continuous = false;

    recognition.onstart = () => {
      setIsListening(true);
      if (window.speechSynthesis) window.speechSynthesis.cancel();
      setIsSpeaking(false);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
      if (event.error === 'not-allowed') {
        alert("마이크 권한이 거부되었습니다.");
      } else if (event.error === 'audio-capture') {
        alert("마이크를 찾을 수 없습니다.");
      }
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (transcript.trim()) {
        setQuery(transcript);
        handleSearch(transcript);
      }
    };

    try {
      recognition.start();
    } catch (e) {
      console.error("Recognition start failed:", e);
      setIsListening(false);
    }
  };

  // TTS (음성 출력) 함수
  const speak = (text) => {
    if (!window.speechSynthesis || !text) return;
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ko-KR';
    utterance.rate = 1.0;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    
    window.speechSynthesis.speak(utterance);
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
      const sessionIdForBackend = isLoggedIn ? user.name : 'guest';
      const res = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: text, 
          top_k: 4,
          session_id: sessionIdForBackend
        }),
      });
      const data = await res.json();
      const aiReport = data.ai_report || data.answer || "보안 관련 질문을 입력해 주세요.";
      
      setMessages(prev => [...prev, { 
        type: 'ai', 
        report: aiReport, 
        results: data.results || [], 
        intent: data.intent_info?.intent || "OOD" 
      }]);
      
      // AI 보고서 자동 읽기
      speak(aiReport);
      
      // 검색 성공 후 히스토리 갱신
      fetchHistory();
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
        <div className="search-box">
          <Search className="search-icon" size={14} />
          <input 
            type="text" 
            placeholder="최근 기록 검색..." 
            value={searchTerm} 
            onChange={(e) => setSearchTerm(e.target.value)} 
          />
        </div>
        <div className="history-section">
          <div className="history-title"><Clock size={12} /><span>최근 검색 기록</span></div>
          <div className="history-section-container" style={{maxHeight: 'calc(100vh - 250px)', overflowY: 'auto'}}>
            {recentSearches
              .filter(item => item.title.toLowerCase().includes(searchTerm.toLowerCase()))
              .map(item => (
              <div key={item.id} className={`history-item group ${currentSessionId === item.id ? 'active' : ''}`} onClick={() => handleHistoryClick(item)} style={{backgroundColor: currentSessionId === item.id ? '#1f2937' : 'transparent', position: 'relative', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <div style={{flex: 1, overflow: 'hidden'}}><div className="item-title" style={{whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: '20px'}}>{item.title}</div><div className="item-info">{item.location} • {item.date}</div></div>
                <button 
                  className="delete-btn" 
                  onClick={(e) => handleDeleteHistory(e, item.id)} 
                  style={{
                    background: 'transparent',
                    border: 'none',
                    padding: '8px',
                    margin: '-8px',
                    cursor: 'pointer',
                    position: 'absolute',
                    right: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 10,
                    opacity: '0.4'
                  }}
                >
                  <X size={14} style={{color: '#6b7280'}} />
                </button>
              </div>
            ))}
          </div>
        </div>
        <div className="user-profile" onClick={isLoggedIn ? () => setShowLogoutModal(true) : () => setShowLoginModal(true)} style={{cursor: 'pointer'}}>
          <div className="avatar" style={{backgroundColor: isLoggedIn ? '#3b82f6' : '#6b7280'}}>{user.name[0]}</div>
          <div style={{flex: 1}}><div style={{fontSize: '13px', fontWeight: '600'}}>{user.name}</div><div style={{fontSize: '10px', color: '#6b7280'}}>{isLoggedIn ? user.role : '로그인 필요'}</div></div>
          {isLoggedIn ? <MoreVertical size={16} /> : <LogIn size={16} />}
        </div>
      </aside>

      <main className="main-content">
        <header className="header">
          <div className="header-logo">Searchlight <MoreVertical size={14} /></div>
          <div style={{display: 'flex', gap: '20px', color: '#9ca3af'}}>
            <User size={18} cursor="pointer" onClick={isLoggedIn ? () => setShowLogoutModal(true) : () => setShowLoginModal(true)} style={{color: isLoggedIn ? '#3b82f6' : '#9ca3af'}} />
            <Settings size={18} cursor="pointer" onClick={() => setShowSettingsModal(true)} className="hover:text-white transition-colors" />
          </div>
        </header>

        <div className="chat-container" style={{flex: 1, overflowY: 'auto', padding: '40px'}}>
          {messages.length === 0 ? (
            <div className="welcome-screen" style={{height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
              <h1 className="welcome-title" style={{fontSize: '28px', textAlign: 'center', lineHeight: '1.5', fontWeight: '300'}}>
                지능형 보안 분석관 <span style={{fontWeight: '700', color: '#3b82f6'}}>SearchLight</span>입니다.<br/>
                <span style={{fontSize: '18px', color: '#9ca3af'}}>CCTV 분석 및 보안 관련 질문을 입력하세요.</span>
              </h1>
            </div>
          ) : (
            <div style={{maxWidth: '800px', margin: '0 auto'}}>
              {messages.map((msg, i) => (
                <div key={i} style={{marginBottom: '30px', display: 'flex', flexDirection: 'column', alignItems: msg.type === 'user' ? 'flex-end' : 'flex-start'}}>
                  {msg.type === 'user' ? (
                    <div style={{backgroundColor: '#3b82f6', padding: '12px 20px', borderRadius: '15px 15px 0 15px', maxWidth: '80%', fontSize: '14px'}}>{msg.text}</div>
                  ) : (
                    <div style={{width: '100%', backgroundColor: msg.intent === 'ERROR' ? '#450a0a' : '#1a2235', padding: '25px', borderRadius: '15px', border: msg.intent === 'ERROR' ? '1px solid #ef4444' : '1px solid rgba(255,255,255,0.1)'}}>
                      <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px', color: msg.intent === 'ERROR' ? '#f87171' : '#3b82f6', fontSize: '13px', fontWeight: 'bold'}}>{msg.intent === 'ERROR' ? <AlertCircle size={16} /> : <Shield size={16} />} {msg.intent === 'ERROR' ? "시스템 오류" : "AI 분석 보고서"}<span style={{flex: 1}}></span><span style={{fontSize: '10px', color: '#6b7280'}}>{msg.intent}</span></div>
                      
                      <div style={{fontSize: '14px', lineHeight: '1.7', color: '#d1d5db', whiteSpace: 'pre-wrap', backgroundColor: 'rgba(255,255,255,0.03)', padding: '15px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.05)'}}>
                        {msg.report}
                      </div>

                      {msg.results?.length > 0 && (
                        <div style={{marginTop: '20px'}}>
                          {settings.viewMode === 'list' ? (
                            <div style={{display: 'flex', flexDirection: 'column', gap: '15px'}}>
                              {msg.results.map((res, j) => {
                                const resultKey = `${i}-${j}`;
                                const isExpanded = expandedResults[resultKey];
                                
                                return (
                                  <div key={j} className="result-card" style={{backgroundColor: '#0b0f19', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.05)', transition: 'all 0.3s ease'}}>
                                    <div style={{display: 'flex', gap: '15px', padding: '12px'}}>
                                      <div style={{width: '140px', height: '100px', borderRadius: '8px', overflow: 'hidden', flexShrink: 0, position: 'relative'}}>
                                        <img src={`http://localhost:8000${res.image_path}`} style={{width: '100%', height: '100%', objectFit: 'cover'}} alt="cctv thumb" />
                                        <div style={{position: 'absolute', bottom: '5px', right: '5px', backgroundColor: 'rgba(0,0,0,0.6)', padding: '2px 6px', borderRadius: '4px', fontSize: '10px', color: '#3b82f6'}}>{(res.score * 100).toFixed(0)}%</div>
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
                                );
                              })}
                            </div>
                          ) : (
                            <div style={{backgroundColor: '#0b0f19', borderRadius: '15px', height: '300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: '2px dashed rgba(59, 130, 246, 0.3)', gap: '15px'}}>
                              <div style={{fontSize: '40px'}}>🗺️</div>
                              <div style={{textAlign: 'center'}}>
                                <div style={{fontSize: '20px', fontWeight: 'bold', color: 'white', marginBottom: '5px'}}>건물 도면 기반 위치 확인 중</div>
                                <div style={{fontSize: '14px', color: '#6b7280'}}>감지된 이벤트 {msg.results.length}건이 지도에 표시됩니다.</div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
              {loading && <div style={{color: '#3b82f6', fontSize: '12px', fontStyle: 'italic'}}>AI 분석 중...</div>}<div ref={chatEndRef} />
            </div>
          )}
        </div>

        <div className="input-area"><div className="input-container" style={{padding: '20px 40px 40px', position: 'relative'}}>
          {(isListening || isSpeaking) && (
            <div className="voice-indicator">
              <div className="waveform">
                {[...Array(5)].map((_, i) => <div key={i} className="bar" style={{animationDelay: `${i * 0.15}s`}}></div>)}
              </div>
              <span>{isListening ? "말씀해 주세요..." : "보고서를 읽어드리는 중입니다..."}</span>
            </div>
          )}
          <div className="input-wrapper">
            <Plus size={20} style={{color: '#6b7280', cursor: 'pointer'}} />
            <input 
              type="text" 
              placeholder="질문을 입력하세요..." 
              value={query} 
              onChange={(e) => setQuery(e.target.value)} 
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()} 
            />
            <button className={`mic-btn ${isListening ? 'listening' : ''}`} onClick={startListening} title="음성 검색">
              <Mic size={20} />
            </button>
            <button className="icon-btn send-btn" onClick={() => handleSearch()} style={{marginLeft: '10px', width: '42px', height: '42px', borderRadius: '10px'}}>
              <Send size={18} />
            </button>
          </div>
        </div></div>
      </main>

      {/* Login Modal */}
      {showLoginModal && (
        <div className="modal-overlay" style={{position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(5px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000}}>
          <div className="modal-content" style={{backgroundColor: '#111827', padding: '40px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)', width: '350px'}}>
            <div style={{display: 'flex', justifyContent: 'center', marginBottom: '20px'}}><div style={{padding: '15px', backgroundColor: '#3b82f6', borderRadius: '15px'}}><Lock size={32} /></div></div>
            <h2 style={{textAlign: 'center', marginBottom: '10px', fontSize: '20px'}}>시스템 관리자 인증</h2>
            <p style={{textAlign: 'center', color: '#6b7280', fontSize: '12px', marginBottom: '30px'}}>계정 정보를 입력해 주세요.</p>
            <form onSubmit={handleLogin}>
              <div style={{marginBottom: '15px'}}><label style={{fontSize: '11px', color: '#9ca3af', marginBottom: '5px', display: 'block'}}>ID</label><input type="text" required value={loginInput.id} onChange={(e) => setLoginInput({...loginInput, id: e.target.value})} style={{width: '100%', backgroundColor: '#1f2937', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '12px', color: 'white'}} placeholder="관리자 아이디" /></div>
              <div style={{marginBottom: '30px'}}><label style={{fontSize: '11px', color: '#9ca3af', marginBottom: '5px', display: 'block'}}>PASSWORD</label><input type="password" required value={loginInput.pw} onChange={(e) => setLoginInput({...loginInput, pw: e.target.value})} style={{width: '100%', backgroundColor: '#1f2937', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '12px', color: 'white'}} placeholder="••••••••" /></div>
              <button type="submit" style={{width: '100%', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '10px', padding: '14px', fontWeight: 'bold', cursor: 'pointer'}}>인증 및 로그인</button>
              <button type="button" onClick={() => setShowLoginModal(false)} style={{width: '100%', background: 'transparent', color: '#6b7280', border: 'none', marginTop: '15px', fontSize: '12px', cursor: 'pointer'}}>닫기</button>
            </form>
          </div>
        </div>
      )}

      {/* Logout Confirmation Modal */}
      {showLogoutModal && (
        <div className="modal-overlay" style={{position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(5px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000}}>
          <div className="modal-content" style={{backgroundColor: '#111827', padding: '40px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)', width: '350px', textAlign: 'center'}}>
            <div style={{display: 'flex', justifyContent: 'center', marginBottom: '20px'}}><div style={{padding: '15px', backgroundColor: '#ef4444', borderRadius: '15px'}}><LogOut size={32} /></div></div>
            <h2 style={{marginBottom: '10px', fontSize: '20px'}}>로그아웃</h2>
            <p style={{color: '#6b7280', fontSize: '12px', marginBottom: '30px'}}>정말 시스템에서 로그아웃 하시겠습니까?</p>
            <div style={{display: 'flex', gap: '10px'}}>
              <button onClick={executeLogout} style={{flex: 1, backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '10px', padding: '14px', fontWeight: 'bold', cursor: 'pointer'}}>로그아웃</button>
              <button onClick={() => setShowLogoutModal(false)} style={{flex: 1, backgroundColor: '#1f2937', color: 'white', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', padding: '14px', fontWeight: 'bold', cursor: 'pointer'}}>취소</button>
            </div>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      {showSettingsModal && (
        <div className="modal-overlay" style={{position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(10px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000}}>
          <div className="modal-content" style={{backgroundColor: '#111827', padding: '25px 30px', borderRadius: '24px', border: '1px solid rgba(255,255,255,0.1)', width: '500px', maxWidth: '95vw', maxHeight: '90vh', overflowY: 'auto'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px'}}>
              <h2 style={{fontSize: '22px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '10px'}}><Settings className="text-blue-500" /> 시스템 설정</h2>
              <X size={24} cursor="pointer" onClick={() => setShowSettingsModal(false)} className="text-gray-500 hover:text-white" />
            </div>

            <div style={{display: 'flex', flexDirection: 'column', gap: '20px'}}>
              <section>
                <h3 style={{fontSize: '16px', color: '#3b82f6', marginBottom: '10px', fontWeight: '600'}}>🚨 보안 알림 설정</h3>
                <div style={{backgroundColor: '#1f2937', padding: '15px', borderRadius: '15px', display: 'flex', flexDirection: 'column', gap: '15px'}}>
                  <div>
                    <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '8px'}}>
                      <span style={{fontSize: '14px'}}>감지 민감도</span>
                      <span style={{fontSize: '14px', color: '#3b82f6', fontWeight: 'bold'}}>{settings.sensitivity}%</span>
                    </div>
                    <input 
                      type="range" 
                      min="1" max="100" 
                      value={settings.sensitivity} 
                      onChange={(e) => setSettings({...settings, sensitivity: e.target.value})}
                      style={{width: '100%', height: '5px', backgroundColor: '#374151', borderRadius: '3px', cursor: 'pointer'}}
                    />
                  </div>
                  <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                    <span style={{fontSize: '14px'}}>경고음 발생</span>
                    <button 
                      onClick={() => setSettings({...settings, enableSound: !settings.enableSound})}
                      style={{
                        width: '44px', height: '22px', borderRadius: '11px', 
                        backgroundColor: settings.enableSound ? '#3b82f6' : '#374151',
                        position: 'relative', transition: 'all 0.3s ease', border: 'none', cursor: 'pointer'
                      }}
                    >
                      <div style={{
                        width: '16px', height: '16px', borderRadius: '50%', backgroundColor: 'white',
                        position: 'absolute', top: '3px', left: settings.enableSound ? '25px' : '3px',
                        transition: 'all 0.3s ease'
                      }}></div>
                    </button>
                  </div>
                </div>
              </section>

              <section>
                <h3 style={{fontSize: '16px', color: '#3b82f6', marginBottom: '10px', fontWeight: '600'}}>📺 화면 레이아웃</h3>
                <div style={{display: 'flex', gap: '10px'}}>
                  <button 
                    onClick={() => setSettings({...settings, viewMode: 'list'})}
                    style={{
                      flex: 1, padding: '15px', borderRadius: '15px', border: settings.viewMode === 'list' ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)',
                      backgroundColor: settings.viewMode === 'list' ? 'rgba(59, 130, 246, 0.1)' : '#1f2937', color: 'white', cursor: 'pointer', transition: 'all 0.2s'
                    }}
                  >
                    <div style={{fontSize: '18px', marginBottom: '4px'}}>📋</div>
                    <div style={{fontSize: '15px', fontWeight: 'bold'}}>목록 형태</div>
                  </button>
                  <button 
                    onClick={() => setSettings({...settings, viewMode: 'map'})}
                    style={{
                      flex: 1, padding: '15px', borderRadius: '15px', border: settings.viewMode === 'map' ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)',
                      backgroundColor: settings.viewMode === 'map' ? 'rgba(59, 130, 246, 0.1)' : '#1f2937', color: 'white', cursor: 'pointer', transition: 'all 0.2s'
                    }}
                  >
                    <div style={{fontSize: '18px', marginBottom: '4px'}}>🗺️</div>
                    <div style={{fontSize: '15px', fontWeight: 'bold'}}>지도 형태</div>
                  </button>
                </div>
              </section>
            </div>

            <button 
              onClick={() => setShowSettingsModal(false)}
              style={{width: '100%', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '12px', padding: '14px', fontWeight: 'bold', fontSize: '16px', marginTop: '20px', cursor: 'pointer'}}
            >
              설정 저장 및 닫기
            </button>
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
        .delete-btn { transition: all 0.2s; }
        .delete-btn:hover { opacity: 1 !important; transform: scale(1.1); }
        .delete-btn:hover svg { color: #ef4444 !important; }
      `}</style>
    </div>
  );
};

export default App;