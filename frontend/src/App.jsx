import React, { useState, useEffect, useRef } from 'react';
import { 
  Plus, Search, Shield, Clock, Settings, User, MoreVertical, LogIn, LogOut, Mic, Square, X, Archive
} from 'lucide-react';

// Hooks
import { useAuth } from './hooks/useAuth';
import { useChat } from './hooks/useChat';
import { useVoice } from './hooks/useVoice';

// Components
import MessageItem from './components/chat/MessageItem';
import ResultCard from './components/chat/ResultCard';
import EventHistory from './components/EventHistory';

const App = () => {
  const { isLoggedIn, user, login, logout } = useAuth();
  const { 
    messages, setMessages, recentSearches, currentSessionId, 
    loading, handleSearch, startNewChat, deleteHistory 
  } = useChat(isLoggedIn, user?.name);
  
  const [query, setQuery] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedResults, setExpandedResults] = useState({});
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [currentView, setCurrentView] = useState('chat');
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const chatEndRef = useRef(null);

  const [sidebarWidth, setSidebarWidth] = useState(260);
  const [isResizing, setIsResizing] = useState(false);

  const { isListening, isSpeaking, startListening, speak } = useVoice((text) => {
    setQuery(text);
    onSearch(text);
  });

  const startResizing = (e) => {
    setIsResizing(true);
    e.preventDefault();
  };

  const stopResizing = () => {
    setIsResizing(false);
  };

  const resize = (e) => {
    if (isResizing) {
      const newWidth = e.clientX;
      if (newWidth > 150 && newWidth < 500) {
        setSidebarWidth(newWidth);
      }
    }
  };

  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', resize);
      window.addEventListener('mouseup', stopResizing);
    } else {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
    }
    return () => {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
    };
  }, [isResizing]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const onSearch = async (text = query) => {
    const report = await handleSearch(text);
    if (report) speak(report);
    setQuery('');
  };

  const handleLoginSubmit = () => {
    if (loginEmail === 'rssgrace11@gmail.com' && loginPassword === '1234') {
      login('관리자', "보안 분석관");
      setLoginEmail('');
      setLoginPassword('');
      setShowLoginModal(false);
    } else {
      alert('아이디 또는 비밀번호가 일치하지 않습니다.');
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar - Simplified for refactoring */}
      <aside className="sidebar" style={{ width: `${sidebarWidth}px`, flexShrink: 0 }}>
        <button className={`new-chat-btn ${currentView === 'archive' ? 'active' : ''}`} style={{ marginBottom: '10px', backgroundColor: currentView === 'archive' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(59, 130, 246, 0.1)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.2)' }} onClick={() => setCurrentView('archive')}><Archive size={18} /><span>영상 보관함</span></button>
        <button className="new-chat-btn" onClick={() => { startNewChat(); setCurrentView('chat'); }}><Plus size={18} /><span>새 채팅</span></button>
        <div className="search-box">
          <Search className="search-icon" size={14} />
          <input type="text" placeholder="최근 기록 검색..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
        </div>
        <div className="history-section">
          <div className="history-title"><Clock size={12} /><span>최근 검색 기록</span></div>
          {recentSearches.filter(item => item.title?.includes(searchTerm)).map((item, idx) => (
            <div key={idx} className="history-item" onClick={() => {
              setMessages(item.messages);
              setExpandedResults({});
              setCurrentSessionId(item.raw_session_id);
            }}>
              <div style={{flex: 1, overflow: 'hidden'}}>
                <div className="item-title">{item.title}</div>
                <div className="item-info">{item.location} • {item.date}</div>
              </div>
              <button 
                className="delete-history-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  if (window.confirm("이 검색 기록을 삭제하시겠습니까?")) {
                    deleteHistory(item.id);
                  }
                }}
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
        <div className="user-profile">
           <div 
             onClick={() => !isLoggedIn && setShowLoginModal(true)} 
             style={{display: 'flex', alignItems: 'center', gap: '12px', flex: 1, cursor: !isLoggedIn ? 'pointer' : 'default'}}
           >
              <div className="avatar">{user?.name ? user.name[0] : '?'}</div>
              <div style={{flex: 1}}>
                <div style={{fontSize: '13px', fontWeight: '600'}}>{user?.name}</div>
                <div style={{fontSize: '10px', color: '#9ca3af'}}>{user?.role}</div>
              </div>
           </div>
           
           {isLoggedIn ? (
             <button 
               className="icon-btn" 
               title="로그아웃"
               onClick={(e) => {
                 e.preventDefault();
                 e.stopPropagation();
                 if (window.confirm("로그아웃 하시겠습니까?")) logout();
               }}
               style={{ cursor: 'pointer', color: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
             >
               <LogOut size={18} />
             </button>
           ) : (
             <button 
               className="icon-btn" 
               onClick={() => setShowLoginModal(true)}
               style={{ cursor: 'pointer', color: '#3b82f6' }}
             >
               <LogIn size={18} />
             </button>
           )}
        </div>
      </aside>

      <div 
        className="resizer" 
        onMouseDown={startResizing}
        style={{
          width: '4px',
          cursor: 'col-resize',
          backgroundColor: isResizing ? '#3b82f6' : 'transparent',
          transition: 'background-color 0.2s',
          zIndex: 10
        }}
      />

      {/* Login Modal */}
      {showLoginModal && (
        <div className="modal-overlay" onClick={() => setShowLoginModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2 className="modal-title">시스템 접속</h2>
            <div style={{marginBottom: '15px'}}>
              <label style={{display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '5px'}}>이메일</label>
              <input 
                className="modal-input"
                value={loginEmail}
                onChange={e => setLoginEmail(e.target.value)}
                placeholder="rssgrace11@gmail.com"
                style={{marginBottom: '0'}}
                autoFocus
              />
            </div>
            <div style={{marginBottom: '20px'}}>
              <label style={{display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '5px'}}>비밀번호</label>
              <input 
                className="modal-input"
                type="password"
                value={loginPassword}
                onChange={e => setLoginPassword(e.target.value)}
                onKeyPress={e => e.key === 'Enter' && handleLoginSubmit()}
                placeholder="****"
                style={{marginBottom: '0'}}
              />
            </div>
            <div className="modal-buttons">
              <button className="modal-btn cancel" onClick={() => setShowLoginModal(false)}>취소</button>
              <button className="modal-btn confirm" onClick={handleLoginSubmit}>접속</button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="main-content" style={{ overflowY: 'auto' }}>
        <header className="header">
          <div className="header-logo" onClick={() => setCurrentView('chat')} style={{cursor: 'pointer'}}><Shield size={18} color="#3b82f6" /> SearchLight <MoreVertical size={14} /></div>
          <div style={{display: 'flex', gap: '20px'}}>
             <Settings size={18} cursor="pointer" className="icon-btn" />
             <User size={18} cursor="pointer" className="icon-btn" />
          </div>
        </header>

        {currentView === 'archive' ? (
          <EventHistory />
        ) : (
          <>
            <div className="chat-container">
          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div style={{width: '60px', height: '60px', backgroundColor: 'rgba(59,130,246,0.1)', borderRadius: '15px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '25px', border: '1px solid rgba(59,130,246,0.2)'}}>
                <Shield size={32} color="#3b82f6" />
              </div>
              <h1 className="welcome-title">지능형 보안 분석관 <b>SearchLight</b></h1>
              <p style={{color: '#9ca3af', fontSize: '18px', fontWeight: '300', marginBottom: '10px'}}>무엇을 도와드릴까요? 사건 사고 및 CCTV 통합 검색을 지원합니다.</p>
              
              <div className="input-container">
                <div className="input-wrapper" style={{position: 'relative'}}>
                  {isListening && (
                    <div className="voice-indicator">
                      <div className="waveform">
                        <div className="bar" style={{animationDelay: '0.1s'}}></div>
                        <div className="bar" style={{animationDelay: '0.2s'}}></div>
                        <div className="bar" style={{animationDelay: '0.3s'}}></div>
                      </div>
                      음성 인식 중...
                    </div>
                  )}
                  <input 
                    value={query} 
                    onChange={(e) => setQuery(e.target.value)} 
                    onKeyPress={(e) => e.key === 'Enter' && onSearch()} 
                    placeholder="보안 상황에 대해 질문하세요 (예: 빨간 옷 입은 사람 찾아줘)" 
                  />
                  <div style={{display: 'flex', gap: '8px'}}>
                    <button 
                      className={`mic-btn ${isListening ? 'listening' : ''}`}
                      onClick={startListening}
                      title="음성 인식"
                    >
                      {isListening ? <Square size={18} fill="white" /> : <Mic size={20} />}
                    </button>
                    <button className="icon-btn send-btn" onClick={() => onSearch()} style={{width: '42px', height: '42px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '10px'}}>
                      <Search size={20} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div style={{maxWidth: '800px', margin: '0 auto', width: '100%', padding: '0 20px'}}>
              {messages.map((msg, i) => (
                <div key={i}>
                  <MessageItem msg={msg} expandedResults={expandedResults} setExpandedResults={setExpandedResults} index={i} sessionId={currentSessionId} />
                  {msg.results?.map((res, j) => (
                    <div key={j} style={{marginBottom: '15px'}}>
                       <ResultCard res={res} resultKey={`${i}-${j}`} isExpanded={expandedResults[`${i}-${j}`]} setExpandedResults={setExpandedResults} />
                    </div>
                  ))}
                </div>
              ))}
              {loading && (
                <div style={{display: 'flex', gap: '10px', alignItems: 'center', color: '#6b7280', fontSize: '13px', marginLeft: '25px'}}>
                  <div className="loader"></div> AI 분석 중...
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          )}
        </div>

        {/* Input Area (Bottom) - Only show when there are messages */}
        {messages.length > 0 && (
          <div className="input-container">
            <div className="input-wrapper" style={{position: 'relative'}}>
              {isListening && (
                <div className="voice-indicator">
                  <div className="waveform">
                    <div className="bar" style={{animationDelay: '0.1s'}}></div>
                    <div className="bar" style={{animationDelay: '0.2s'}}></div>
                    <div className="bar" style={{animationDelay: '0.3s'}}></div>
                  </div>
                  음성 인식 중...
                </div>
              )}
              <input 
                value={query} 
                onChange={(e) => setQuery(e.target.value)} 
                onKeyPress={(e) => e.key === 'Enter' && onSearch()} 
                placeholder="보안 상황에 대해 질문하세요..." 
              />
              <div style={{display: 'flex', gap: '8px'}}>
                <button 
                  className={`mic-btn ${isListening ? 'listening' : ''}`}
                  onClick={startListening}
                  title="음성 인식"
                >
                  {isListening ? <Square size={18} fill="white" /> : <Mic size={20} />}
                </button>
                <button className="icon-btn send-btn" onClick={() => onSearch()} style={{width: '42px', height: '42px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '10px'}}>
                  <Search size={20} />
                </button>
              </div>
            </div>
          </div>
        )}
        </>
        )}
      </main>
      
      <style>{`
        .loader { width: 16px; height: 16px; border: 2px solid #3b82f6; border-top: 2px solid transparent; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

export default App;