import { useState, useEffect, useRef } from 'react';

const API_BASE = 'http://localhost:8000';

export function useChat(user, isLoggedIn) {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [recentSearches, setRecentSearches] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const chatEndRef = useRef(null);

  // 자동 스크롤
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 현재 세션 메시지 로컬 동기화
  useEffect(() => {
    if (currentSessionId && messages.length > 0) {
      setRecentSearches(prev =>
        prev.map(s => s.id === currentSessionId ? { ...s, messages } : s)
      );
    }
  }, [messages, currentSessionId]);

  const fetchHistory = async () => {
    try {
      const sessionId = isLoggedIn ? user.name : 'guest';
      const res = await fetch(`${API_BASE}/api/history/${sessionId}`);
      const data = await res.json();
      if (data.status === 'success' && data.history) {
        const formatted = data.history.map(item => ({
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
        setRecentSearches(formatted);
      }
    } catch (error) {
      console.error('히스토리 로딩 실패:', error);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [isLoggedIn, user.name]);

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setQuery('');
  };

  const handleHistoryClick = (session) => {
    setCurrentSessionId(session.id);
    if (session.messages?.length > 0) {
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

  const handleSearch = async (text = query) => {
    if (!text?.trim()) return;
    let sid = currentSessionId;
    if (!sid) {
      sid = Date.now();
      setRecentSearches(prev => [
        { id: sid, title: text, messages: [], location: '실시간 관제', date: new Date().toLocaleDateString(), user: user.name },
        ...prev
      ]);
      setCurrentSessionId(sid);
    }
    setMessages(prev => [...prev, { type: 'user', text }]);
    setQuery('');
    setLoading(true);
    try {
      const sessionId = isLoggedIn ? user.name : 'guest';
      const res = await fetch(`${API_BASE}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, top_k: 1, session_id: sessionId }),
      });
      const data = await res.json();
      const aiMsg = {
        type: 'ai',
        report: data.ai_report || data.answer || '보안 관련 질문을 입력해 주세요.',
        results: data.results || [],
        intent: data.intent_info?.intent || 'OOD',
        mode: data.response_mode || 'summary'
      };
      setMessages(prev => [...prev, aiMsg]);
      fetchHistory();
    } catch (error) {
      setMessages(prev => [...prev, { type: 'ai', report: '서버 연결 오류가 발생했습니다.', intent: 'ERROR' }]);
    } finally {
      setLoading(false);
    }
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

  return {
    query, setQuery,
    messages, loading,
    currentSessionId,
    recentSearches,
    isListening,
    chatEndRef,
    handleNewChat,
    handleHistoryClick,
    handleDeleteHistory,
    handleSearch,
    startListening,
  };
}
