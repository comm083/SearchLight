import { useState, useEffect, useCallback } from 'react';

export const useChat = (isLoggedIn, userName) => {
  const [messages, setMessages] = useState([]);
  const [recentSearches, setRecentSearches] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchHistory = useCallback(async () => {
    try {
      const fetchFrom = ['guest'];
      if (isLoggedIn && userName && userName !== '방문객') {
        fetchFrom.push(userName);
      }

      let combinedHistory = [];
      for (const uid of fetchFrom) {
        try {
          const res = await fetch(`http://localhost:8000/api/history/${uid}`);
          const data = await res.json();
          if (data.status === 'success' && data.history) {
            combinedHistory = [...combinedHistory, ...data.history];
          }
        } catch (e) {
          console.error(`히스토리 로딩 실패 (${uid}):`, e);
        }
      }

      // 날짜순 정렬 (최신순)
      combinedHistory.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

      // 중복 제거 (id 기준)
      const uniqueHistory = combinedHistory.filter((item, index, self) =>
        index === self.findIndex((t) => t.id === item.id)
      );

      const formattedHistory = uniqueHistory.map(item => ({
        id: item.id,
        title: item.query || "(제목 없음)",
        location: item.intent,
        date: new Date(item.created_at).toLocaleDateString(),
        ai_report: item.ai_report,
        messages: [
          { type: 'user', text: item.query },
          { type: 'ai', report: item.ai_report, intent: item.intent }
        ]
      }));
      setRecentSearches(formattedHistory);
    } catch (error) {
      console.error("전체 히스토리 로딩 실패:", error);
    }
  }, [isLoggedIn, userName]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleSearch = async (text) => {
    if (!text?.trim()) return;

    let sessionId = currentSessionId;
    if (!sessionId) {
      sessionId = Date.now();
      setCurrentSessionId(sessionId);
    }

    setMessages(prev => [...prev, { type: 'user', text }]);
    setLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: text, 
          session_id: isLoggedIn ? userName : 'guest' 
        }),
      });
      const data = await res.json();
      
      const aiMsg = { 
        type: 'ai', 
        report: data.ai_report || data.answer, 
        results: data.results || [], 
        intent: data.intent_info?.intent || "OOD",
        mode: data.response_mode || "summary"
      };
      
      setMessages(prev => [...prev, aiMsg]);
      fetchHistory();
      return aiMsg.report; // For TTS
    } catch (error) {
      setMessages(prev => [...prev, { type: 'ai', report: "오류가 발생했습니다.", intent: "ERROR" }]);
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
  };

  const deleteHistory = async (historyId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/history/${historyId}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (data.status === 'success') {
        // 로컬 상태 업데이트
        setRecentSearches(prev => prev.filter(item => item.id !== historyId));
        return true;
      }
      return false;
    } catch (error) {
      console.error("히스토리 삭제 실패:", error);
      return false;
    }
  };

  return { 
    messages, setMessages, recentSearches, setRecentSearches, 
    currentSessionId, setCurrentSessionId, loading, 
    handleSearch, startNewChat, deleteHistory 
  };
};
