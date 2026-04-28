import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Search, ShieldAlert, Camera, History, UserCheck, AlertTriangle, MessageSquare, Loader2, Sparkles, Mic, Volume2, Square } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const INTENT_ICONS = {
  SEARCH: { icon: Search, color: "text-blue-400", bg: "bg-blue-400/10", label: "조회" },
  EMERGENCY: { icon: ShieldAlert, color: "text-red-400", bg: "bg-red-400/10", label: "위험" },
  ERROR: { icon: AlertTriangle, color: "text-yellow-400", bg: "bg-yellow-400/10", label: "장애" },
  ACCESS: { icon: UserCheck, color: "text-green-400", bg: "bg-green-400/10", label: "출입" },
  GENERAL: { icon: MessageSquare, color: "text-purple-400", bg: "bg-purple-400/10", label: "일상" },
  CHITCHAT: { icon: MessageSquare, color: "text-pink-400", bg: "bg-pink-400/10", label: "잡담" }
};

function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const recognitionRef = useRef(null);

  // 음성 인식 설정 (Web Speech API)
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.lang = 'ko-KR';
      recognition.interimResults = false;
      recognition.continuous = false;

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setQuery(transcript);
        executeSearch(transcript);
      };
      recognitionRef.current = recognition;
    }
  }, []);

  const startListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      // 말하기 중단
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      recognitionRef.current?.start();
    }
  };

  // 음성 출력 (TTS)
  const speak = (text) => {
    if (!window.speechSynthesis || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ko-KR';
    utterance.rate = 1.0;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  };

  const handleSearch = (e) => {
    if (e) e.preventDefault();
    executeSearch(query);
  };

  const executeSearch = async (searchQuery) => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('http://localhost:8000/api/search', { query: searchQuery });
      const data = response.data;
      setResult(data);
      
      // 결과 수신 시 자동으로 AI 보고서 또는 답변 읽어주기
      if (data.ai_report) {
        speak(data.ai_report);
      } else if (data.answer) {
        speak(data.answer);
      }
    } catch (err) {
      console.error(err);
      setError("서버와의 통신 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-slate-100 p-6 md:p-12 selection:bg-blue-500/30">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-2"
          >
            <div className="flex items-center gap-2 text-blue-500 font-bold tracking-tight">
              <Sparkles size={20} />
              <span>AI CCTV ANALYTICS</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-black tracking-tighter">
              Search<span className="text-blue-500">Light</span>
            </h1>
            <p className="text-slate-400 font-medium">자연어 질의를 통한 CCTV 지능형 의미 검색 시스템</p>
          </motion.div>

          <div className="flex gap-4">
            <div className="glass-card px-4 py-2 rounded-2xl flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm font-semibold text-slate-300">System Online</span>
            </div>
          </div>
        </header>

        {/* Search Bar */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative mb-12"
        >
          <form onSubmit={handleSearch} className="group">
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="무엇을 찾아드릴까요? (예: 빨간 옷 입은 사람 찾아줘)"
              className="w-full bg-[#161618] border border-white/5 rounded-3xl px-8 py-6 text-xl outline-none focus:border-blue-500/50 transition-all placeholder:text-slate-600 pr-48 shadow-2xl"
            />
            <div className="absolute right-3 top-3 bottom-3 flex gap-2">
              <button
                type="button"
                onClick={startListening}
                className={`w-14 rounded-2xl flex items-center justify-center transition-all ${
                  isListening ? 'bg-red-500 mic-pulse' : 'bg-white/5 hover:bg-white/10 text-slate-400'
                }`}
              >
                {isListening ? <Square size={20} fill="currentColor" /> : <Mic size={20} />}
              </button>
              <button 
                type="submit"
                disabled={loading}
                className="px-8 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 rounded-2xl flex items-center gap-2 font-bold transition-all"
              >
                {loading ? <Loader2 className="animate-spin" /> : <Search size={20} />}
                <span>검색</span>
              </button>
            </div>
          </form>

          {/* Voice Feedback Overlay */}
          <AnimatePresence>
            {(isListening || isSpeaking) && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute -bottom-16 left-1/2 -translate-x-1/2 flex items-center gap-4 px-6 py-3 glass-card rounded-2xl border-blue-500/30"
              >
                <div className="flex items-center gap-1 h-6">
                  {[...Array(8)].map((_, i) => (
                    <div key={i} className="waveform-bar" style={{ animationDelay: `${i * 0.1}s` }} />
                  ))}
                </div>
                <span className="text-sm font-bold text-blue-400">
                  {isListening ? "말씀해 주세요..." : "AI가 설명하는 중입니다..."}
                </span>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Content Area */}
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div 
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-24 gap-4"
            >
              <div className="relative ai-glow">
                <div className="p-8 bg-blue-600/20 rounded-full">
                  <Loader2 size={48} className="text-blue-500 animate-spin" />
                </div>
                <div className="absolute inset-0 bg-blue-500 blur-3xl opacity-20 animate-pulse" />
              </div>
              <p className="text-slate-200 font-bold text-lg animate-pulse">AI가 실시간 CCTV 데이터를 분석하고 있습니다...</p>
              <p className="text-slate-500 text-sm">잠시만 기다려 주세요.</p>
            </motion.div>
          ) : result ? (
            <motion.div 
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-8"
            >
              {/* Intent & AI Report Section */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-1 flex items-center gap-4 p-6 glass-card rounded-3xl">
                  {result.intent_info && (
                    <>
                      <div className={`p-4 rounded-2xl ${INTENT_ICONS[result.intent_info.intent]?.bg || 'bg-slate-400/10'}`}>
                        {(() => {
                          const Icon = INTENT_ICONS[result.intent_info.intent]?.icon || MessageSquare;
                          return <Icon className={INTENT_ICONS[result.intent_info.intent]?.color || 'text-slate-400'} size={28} />;
                        })()}
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Detected Intent</span>
                          <span className="text-[10px] bg-white/5 px-2 py-0.5 rounded-full text-slate-400">Confidence {Math.round(result.intent_info.confidence * 100)}%</span>
                        </div>
                        <h2 className="text-2xl font-bold">
                          <span className={INTENT_ICONS[result.intent_info.intent]?.color}>{INTENT_ICONS[result.intent_info.intent]?.label || result.intent_info.intent}</span>
                        </h2>
                      </div>
                    </>
                  )}
                </div>

                {/* AI Report Card */}
                {(result.ai_report || result.answer) && (
                  <div className="lg:col-span-2 p-6 glass-card rounded-3xl border-blue-500/20 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                      <Volume2 size={80} className="text-blue-500" />
                    </div>
                    <div className="flex items-center gap-2 mb-4">
                      <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                      <span className="text-xs font-bold text-blue-500 uppercase tracking-widest">AI Security Report</span>
                    </div>
                    <div className="text-lg text-slate-200 leading-relaxed font-medium">
                      {result.ai_report || result.answer}
                    </div>
                    {isSpeaking && (
                      <div className="mt-4 flex items-center gap-2">
                        <div className="waveform-bar" style={{ animationDelay: '0s' }} />
                        <div className="waveform-bar" style={{ animationDelay: '0.2s' }} />
                        <div className="waveform-bar" style={{ animationDelay: '0.4s' }} />
                        <span className="text-xs text-blue-400 font-bold">음성 안내 중...</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Grid Section */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {result.status === "success" && result.results.length > 0 ? (
                  result.results.map((item, idx) => (
                    <motion.div 
                      key={idx}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: idx * 0.1 }}
                      className="group glass-card rounded-[32px] overflow-hidden flex flex-col border border-white/5 hover:border-blue-500/30 transition-all"
                    >
                      <div className="relative aspect-video bg-slate-900 overflow-hidden">
                        {item.image_path ? (
                          <img 
                            src={item.image_path} 
                            alt={item.description}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                          />
                        ) : (
                          <div className="w-full h-full flex flex-col items-center justify-center text-slate-700 gap-2">
                            <Camera size={48} />
                            <span className="text-sm font-medium">No Image Preview</span>
                          </div>
                        )}
                        <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-md px-3 py-1 rounded-full text-xs font-bold text-white border border-white/10">
                          Rank #{item.rank}
                        </div>
                        <div className="absolute bottom-0 left-0 right-0 h-1/2 bg-gradient-to-t from-[#0a0a0b] to-transparent" />
                      </div>
                      <div className="p-6 pt-2">
                        <div className="flex items-center gap-2 mb-3">
                          <History size={14} className="text-blue-500" />
                          <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Similarity Match: {Math.round((1 - item.distance) * 100)}%</span>
                        </div>
                        <p className="text-lg font-bold text-slate-200 leading-snug group-hover:text-white transition-colors">
                          {item.description}
                        </p>
                      </div>
                    </motion.div>
                  ))
                ) : result.status === "blocked" ? (
                  <div className="col-span-full p-12 glass-card rounded-[32px] flex flex-col items-center text-center gap-4">
                    <div className="p-6 bg-yellow-400/10 rounded-full text-yellow-400">
                      <AlertTriangle size={48} />
                    </div>
                    <div className="space-y-2">
                      <h3 className="text-2xl font-bold">요청이 제한되었습니다</h3>
                      <p className="text-slate-400 max-w-md">{result.message}</p>
                    </div>
                  </div>
                ) : (
                  <div className="col-span-full py-24 text-center text-slate-500 italic">
                    일치하는 결과가 없습니다. 다른 검색어를 입력해보세요.
                  </div>
                )}
              </div>
            </motion.div>
          ) : (
            <motion.div 
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-24 text-center gap-6"
            >
              <div className="w-24 h-24 bg-white/5 rounded-full flex items-center justify-center text-slate-700 border border-white/5">
                <Search size={48} />
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-slate-300">검색을 시작하세요</h3>
                <p className="text-slate-500 max-w-xs mx-auto">상황, 인상착의, 특정 이벤트 등을 자연스럽게 입력하여 검색할 수 있습니다.</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default App;