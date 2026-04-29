import React, { useState } from 'react';
import { Mic, Send, Plus, Settings, User, MoreVertical } from 'lucide-react';

// 커스텀 훅
import { useAuth } from './hooks/useAuth';
import { useChat } from './hooks/useChat';

// 컴포넌트
import ChatSidebar from './components/ChatSidebar';
import ChatArea from './components/ChatArea';
import SettingsModal from './components/SettingsModal';
import { LoginModal, LogoutModal } from './components/AuthModals';

const App = () => {
  const auth = useAuth();
  const chat = useChat(auth.user, auth.isLoggedIn);
  const [searchTerm, setSearchTerm] = useState('');
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [settings, setSettings] = useState({
    sensitivity: 70,
    enableSound: true,
    viewMode: 'list',
    autoDeleteDays: 30,
  });

  return (
    <div className="app-container">
      {/* 사이드바 */}
      <ChatSidebar
        isLoggedIn={auth.isLoggedIn}
        user={auth.user}
        recentSearches={chat.recentSearches}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        currentSessionId={chat.currentSessionId}
        onNewChat={chat.handleNewChat}
        onHistoryClick={chat.handleHistoryClick}
        onDeleteHistory={chat.handleDeleteHistory}
        onUserClick={auth.isLoggedIn ? () => auth.setShowLogoutModal(true) : () => auth.setShowLoginModal(true)}
      />

      {/* 메인 콘텐츠 */}
      <main className="main-content">
        <header className="header">
          <div className="header-logo">Searchlight <MoreVertical size={14} /></div>
          <div style={{ display: 'flex', gap: '20px', color: '#9ca3af' }}>
            <User size={18} cursor="pointer"
              onClick={auth.isLoggedIn ? () => auth.setShowLogoutModal(true) : () => auth.setShowLoginModal(true)}
              style={{ color: auth.isLoggedIn ? '#3b82f6' : '#9ca3af' }} />
            <Settings size={18} cursor="pointer" onClick={() => setShowSettingsModal(true)} />
          </div>
        </header>

        {/* 채팅 영역 */}
        <ChatArea
          messages={chat.messages}
          loading={chat.loading}
          chatEndRef={chat.chatEndRef}
          viewMode={settings.viewMode}
        />

        {/* 입력 영역 */}
        <div className="input-area">
          <div className="input-container" style={{ padding: '20px 40px 40px' }}>
            <div className="input-wrapper">
              <Plus size={20} style={{ color: '#6b7280', cursor: 'pointer' }} />
              <input
                type="text"
                placeholder="질문을 입력하세요..."
                value={chat.query}
                onChange={(e) => chat.setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && chat.handleSearch()}
              />
              <Mic size={20} className="icon-btn" onClick={chat.startListening}
                style={{ color: chat.isListening ? '#3b82f6' : '#6b7280' }} />
              <button className="icon-btn send-btn" onClick={() => chat.handleSearch()} style={{ marginLeft: '10px' }}>
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* 모달 */}
      {auth.showLoginModal && (
        <LoginModal
          loginInput={auth.loginInput}
          setLoginInput={auth.setLoginInput}
          onLogin={auth.handleLogin}
          onClose={() => auth.setShowLoginModal(false)}
        />
      )}
      {auth.showLogoutModal && (
        <LogoutModal
          onConfirm={auth.executeLogout}
          onClose={() => auth.setShowLogoutModal(false)}
        />
      )}
      {showSettingsModal && (
        <SettingsModal
          settings={settings}
          setSettings={setSettings}
          onClose={() => setShowSettingsModal(false)}
        />
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