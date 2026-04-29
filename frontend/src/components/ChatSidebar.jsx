import React from 'react';
import { Plus, Search, Clock, User, MoreVertical, LogIn, X } from 'lucide-react';

const ChatSidebar = ({
  isLoggedIn, user,
  recentSearches, searchTerm, setSearchTerm,
  currentSessionId,
  onNewChat, onHistoryClick, onDeleteHistory,
  onUserClick,
}) => (
  <aside className="sidebar">
    <button className="new-chat-btn" onClick={onNewChat}>
      <Plus size={18} /><span>새 채팅</span>
    </button>

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
      <div className="history-section-container" style={{ maxHeight: 'calc(100vh - 250px)' }}>
        {recentSearches
          .filter(item => item.title.toLowerCase().includes(searchTerm.toLowerCase()))
          .map(item => (
            <div
              key={item.id}
              className={`history-item group ${currentSessionId === item.id ? 'active' : ''}`}
              onClick={() => onHistoryClick(item)}
              style={{ backgroundColor: currentSessionId === item.id ? '#1f2937' : 'transparent', position: 'relative', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <div className="item-title" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: '20px' }}>{item.title}</div>
                <div className="item-info">{item.location} • {item.date}</div>
              </div>
              <button
                className="delete-btn"
                onClick={(e) => onDeleteHistory(e, item.id)}
                style={{ background: 'transparent', border: 'none', padding: '8px', margin: '-8px', cursor: 'pointer', position: 'absolute', right: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10, opacity: '0.4' }}
              >
                <X size={14} style={{ color: '#6b7280' }} />
              </button>
            </div>
          ))}
      </div>
    </div>

    <div className="user-profile" onClick={onUserClick} style={{ cursor: 'pointer' }}>
      <div className="avatar" style={{ backgroundColor: isLoggedIn ? '#3b82f6' : '#6b7280' }}>{user.name[0]}</div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: '13px', fontWeight: '600' }}>{user.name}</div>
        <div style={{ fontSize: '10px', color: '#6b7280' }}>{isLoggedIn ? user.role : '로그인 필요'}</div>
      </div>
      {isLoggedIn ? <MoreVertical size={16} /> : <LogIn size={16} />}
    </div>
  </aside>
);

export default ChatSidebar;
