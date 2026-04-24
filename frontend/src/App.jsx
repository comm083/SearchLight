import { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, ShieldAlert, Camera, History, UserCheck, AlertTriangle, MessageSquare, Loader2, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const INTENT_ICONS = {
  SEARCH: { icon: Search, color: "text-blue-400", bg: "bg-blue-400/10", label: "조회" },
  EMERGENCY: { icon: ShieldAlert, color: "text-red-400", bg: "bg-red-400/10", label: "위험" },
  ERROR: { icon: AlertTriangle, color: "text-yellow-400", bg: "bg-yellow-400/10", label: "장애" },
  ACCESS: { icon: UserCheck, color: "text-green-400", bg: "bg-green-400/10", label: "출입" },
  GENERAL: { icon: MessageSquare, color: "text-purple-400", bg: "bg-purple-400/10", label: "일상" }
};

function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('/api/search', { query });
      setResult(response.data);
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
              className="w-full bg-[#161618] border border-white/5 rounded-3xl px-8 py-6 text-xl outline-none focus:border-blue-500/50 transition-all placeholder:text-slate-600 pr-32 shadow-2xl"
            />
            <button 
              type="submit"
              disabled={loading}
              className="absolute right-3 top-3 bottom-3 px-8 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 rounded-2xl flex items-center gap-2 font-bold transition-all"
            >
              {loading ? <Loader2 className="animate-spin" /> : <Search size={20} />}
              <span>검색</span>
            </button>
          </form>
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
              <div className="relative">
                <Loader2 size={48} className="text-blue-500 animate-spin" />
                <div className="absolute inset-0 bg-blue-500 blur-2xl opacity-20 animate-pulse" />
              </div>
              <p className="text-slate-400 font-medium animate-pulse">AI가 영상을 분석하고 의도를 파악하고 있습니다...</p>
            </motion.div>
          ) : result ? (
            <motion.div 
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-8"
            >
              {/* Intent Section */}
              <div className="flex items-center gap-4 p-6 glass-card rounded-3xl">
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
                        의도: <span className={INTENT_ICONS[result.intent_info.intent]?.color}>{INTENT_ICONS[result.intent_info.intent]?.label || result.intent_info.intent}</span>
                      </h2>
                    </div>
                  </>
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