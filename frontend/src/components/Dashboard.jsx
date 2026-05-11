import React, { useState, useEffect, useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import { AlertTriangle, Activity, Clock, TrendingUp } from 'lucide-react';
import axios from 'axios';

const SITUATION_LABELS = {
  assault: '폭행',
  break: '기물파손',
  falling: '쓰러짐',
  smoking: '흡연',
  theft: '절도',
  normal: '정상',
};

const SITUATION_COLORS = {
  assault: '#ef4444',
  break: '#f97316',
  falling: '#eab308',
  smoking: '#a855f7',
  theft: '#3b82f6',
  normal: '#6b7280',
};

const getRawDate = (ts) => {
  if (!ts) return '';
  return ts.replace('T', ' ').replace(/\.\d+/, '').replace(/([+-]\d{2}:\d{2}|Z)$/, '').split(' ')[0];
};

const getHour = (ts) => {
  if (!ts) return -1;
  const clean = ts.replace('T', ' ').replace(/\.\d+/, '').replace(/([+-]\d{2}:\d{2}|Z)$/, '');
  const parts = clean.split(' ');
  if (parts.length < 2) return -1;
  return parseInt(parts[1].split(':')[0], 10);
};

const getWeekLabel = (ts) => {
  const dateStr = getRawDate(ts);
  if (!dateStr) return '';
  const [y, m, d] = dateStr.split('-').map(Number);
  const date = new Date(y, m - 1, d);
  const day = date.getDay();
  const mon = new Date(date);
  mon.setDate(date.getDate() - ((day + 6) % 7));
  const my = mon.getFullYear();
  const mm = String(mon.getMonth() + 1).padStart(2, '0');
  const md = String(mon.getDate()).padStart(2, '0');
  return `${my}-${mm}-${md}`;
};

const getMonthLabel = (ts) => {
  const date = getRawDate(ts);
  return date ? date.substring(0, 7) : '';
};

const VIEW_MODES = [
  { label: '일별', value: 'daily' },
  { label: '주간', value: 'weekly' },
  { label: '월별', value: 'monthly' },
];

const cardStyle = {
  background: 'rgba(255,255,255,0.03)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: '12px',
  padding: '24px',
};

const tooltipStyle = {
  contentStyle: {
    background: '#1f2937',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '8px',
    color: '#f9fafb',
    fontSize: '13px',
  },
};

const Dashboard = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [periodMode, setPeriodMode] = useState('daily');

  useEffect(() => {
    axios.get('/api/alerts/events?limit=1000')
      .then(r => setEvents(Array.isArray(r.data) ? r.data : []))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, []);

  const abnormalEvents = useMemo(() => events.filter(e => e.tag !== 'normal'), [events]);

  const topSituation = useMemo(() => {
    const counts = {};
    for (const e of abnormalEvents) counts[e.tag] = (counts[e.tag] || 0) + 1;
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    return top ? (SITUATION_LABELS[top[0]] || top[0]) : '-';
  }, [abnormalEvents]);

  const peakHour = useMemo(() => {
    const counts = Array(24).fill(0);
    for (const e of abnormalEvents) {
      const h = getHour(e.timestamp);
      if (h >= 0) counts[h]++;
    }
    const max = Math.max(...counts);
    return max === 0 ? '-' : `${counts.indexOf(max)}시`;
  }, [abnormalEvents]);

  const frequencyData = useMemo(() => {
    const map = {};
    for (const e of events) {
      let label;
      if (periodMode === 'daily') label = getRawDate(e.timestamp);
      else if (periodMode === 'weekly') label = getWeekLabel(e.timestamp);
      else label = getMonthLabel(e.timestamp);
      if (!label) continue;
      if (!map[label]) map[label] = { date: label, 이상: 0, 정상: 0 };
      if (e.tag === 'normal') map[label].정상++;
      else map[label].이상++;
    }
    return Object.values(map).sort((a, b) => a.date.localeCompare(b.date));
  }, [events, periodMode]);

  const situationData = useMemo(() => {
    const counts = {};
    for (const e of events) {
      const label = SITUATION_LABELS[e.tag] || e.tag;
      counts[label] = (counts[label] || 0) + 1;
    }
    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
  }, [events]);

  const hourlyData = useMemo(() => {
    const counts = Array(24).fill(0);
    for (const e of abnormalEvents) {
      const h = getHour(e.timestamp);
      if (h >= 0) counts[h]++;
    }
    return counts.map((count, hour) => ({ hour: `${hour}시`, count }));
  }, [abnormalEvents]);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: '#9ca3af' }}>
        데이터 로딩 중...
      </div>
    );
  }

  return (
    <div style={{ padding: '28px 32px', maxWidth: '1100px', margin: '0 auto' }}>
      <h2 style={{ fontSize: '18px', fontWeight: '700', color: '#f9fafb', marginBottom: '24px', letterSpacing: '-0.3px' }}>
        이상 행동 통계 대시보드
      </h2>

      {/* KPI 카드 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '28px' }}>
        {[
          { label: '총 이벤트', value: events.length, icon: <Activity size={18} />, color: '#3b82f6' },
          { label: '이상 이벤트', value: abnormalEvents.length, icon: <AlertTriangle size={18} />, color: '#ef4444' },
          { label: '최빈 상황', value: topSituation, icon: <TrendingUp size={18} />, color: '#f97316' },
          { label: '위험 집중 시간', value: peakHour, icon: <Clock size={18} />, color: '#a855f7' },
        ].map(({ label, value, icon, color }) => (
          <div key={label} style={{ ...cardStyle, padding: '18px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '7px', color, marginBottom: '10px', fontSize: '12px', fontWeight: '500' }}>
              {icon} {label}
            </div>
            <div style={{ fontSize: '26px', fontWeight: '700', color: '#f9fafb' }}>{value}</div>
          </div>
        ))}
      </div>

      {/* 빈도 차트 */}
      <div style={{ ...cardStyle, marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ color: '#f9fafb', fontWeight: '600', fontSize: '14px', margin: 0 }}>이벤트 발생 빈도</h3>
          <div style={{ display: 'flex', gap: '6px' }}>
            {VIEW_MODES.map(m => (
              <button
                key={m.value}
                onClick={() => setPeriodMode(m.value)}
                style={{
                  padding: '4px 12px', borderRadius: '6px', fontSize: '12px', cursor: 'pointer',
                  border: '1px solid',
                  borderColor: periodMode === m.value ? '#3b82f6' : 'rgba(255,255,255,0.1)',
                  background: periodMode === m.value ? 'rgba(59,130,246,0.15)' : 'transparent',
                  color: periodMode === m.value ? '#60a5fa' : '#9ca3af',
                }}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={frequencyData} margin={{ top: 4, right: 4, bottom: 4, left: -16 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} tickLine={false} axisLine={false} />
            <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
            <Tooltip {...tooltipStyle} />
            <Bar dataKey="이상" fill="#ef4444" radius={[3, 3, 0, 0]} maxBarSize={40} />
            <Bar dataKey="정상" fill="#3b82f6" radius={[3, 3, 0, 0]} maxBarSize={40} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* 하단 2열 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: '24px' }}>
        {/* 파이 차트 */}
        <div style={cardStyle}>
          <h3 style={{ color: '#f9fafb', fontWeight: '600', fontSize: '14px', marginBottom: '16px', marginTop: 0 }}>
            상황 유형별 분포
          </h3>
          <ResponsiveContainer width="100%" height={230}>
            <PieChart>
              <Pie
                data={situationData}
                cx="50%"
                cy="45%"
                innerRadius={52}
                outerRadius={82}
                paddingAngle={3}
                dataKey="value"
              >
                {situationData.map((entry, i) => {
                  const origTag = Object.entries(SITUATION_LABELS).find(([, v]) => v === entry.name)?.[0] || entry.name;
                  const color = SITUATION_COLORS[origTag] || '#6b7280';
                  return <Cell key={i} fill={color} />;
                })}
              </Pie>
              <Tooltip {...tooltipStyle} />
              <Legend
                formatter={(v) => <span style={{ color: '#9ca3af', fontSize: '12px' }}>{v}</span>}
                iconSize={10}
                wrapperStyle={{ paddingTop: '8px' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* 시간대별 막대 */}
        <div style={cardStyle}>
          <h3 style={{ color: '#f9fafb', fontWeight: '600', fontSize: '14px', marginBottom: '16px', marginTop: 0 }}>
            시간대별 이상 이벤트
          </h3>
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={hourlyData} margin={{ top: 4, right: 4, bottom: 4, left: -16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="hour" tick={{ fill: '#6b7280', fontSize: 10 }} tickLine={false} axisLine={false} interval={3} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="count" name="이상 이벤트" fill="#f97316" radius={[3, 3, 0, 0]} maxBarSize={24} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
