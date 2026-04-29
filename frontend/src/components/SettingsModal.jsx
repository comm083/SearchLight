import React from 'react';
import { Settings, X } from 'lucide-react';

const SettingsModal = ({ settings, setSettings, onClose }) => (
  <div className="modal-overlay" style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(10px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
    <div className="modal-content" style={{ backgroundColor: '#111827', padding: '25px 30px', borderRadius: '24px', border: '1px solid rgba(255,255,255,0.1)', width: '500px', maxWidth: '95vw', maxHeight: '90vh', overflowY: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '22px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '10px' }}><Settings className="text-blue-500" /> 시스템 설정</h2>
        <X size={24} cursor="pointer" onClick={onClose} className="text-gray-500 hover:text-white" />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* 보안 알림 설정 */}
        <section>
          <h3 style={{ fontSize: '16px', color: '#3b82f6', marginBottom: '10px', fontWeight: '600' }}>🚨 보안 알림 설정</h3>
          <div style={{ backgroundColor: '#1f2937', padding: '15px', borderRadius: '15px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '14px' }}>감지 민감도</span>
                <span style={{ fontSize: '14px', color: '#3b82f6', fontWeight: 'bold' }}>{settings.sensitivity}%</span>
              </div>
              <input type="range" min="1" max="100" value={settings.sensitivity}
                onChange={(e) => setSettings({ ...settings, sensitivity: e.target.value })}
                style={{ width: '100%', height: '5px', backgroundColor: '#374151', borderRadius: '3px', cursor: 'pointer' }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '14px' }}>경고음 발생</span>
              <button onClick={() => setSettings({ ...settings, enableSound: !settings.enableSound })}
                style={{ width: '44px', height: '22px', borderRadius: '11px', backgroundColor: settings.enableSound ? '#3b82f6' : '#374151', position: 'relative', transition: 'all 0.3s ease', border: 'none', cursor: 'pointer' }}>
                <div style={{ width: '16px', height: '16px', borderRadius: '50%', backgroundColor: 'white', position: 'absolute', top: '3px', left: settings.enableSound ? '25px' : '3px', transition: 'all 0.3s ease' }}></div>
              </button>
            </div>
          </div>
        </section>

        {/* 화면 레이아웃 */}
        <section>
          <h3 style={{ fontSize: '16px', color: '#3b82f6', marginBottom: '10px', fontWeight: '600' }}>📺 화면 레이아웃</h3>
          <div style={{ display: 'flex', gap: '10px' }}>
            {['list', 'map'].map(mode => (
              <button key={mode} onClick={() => setSettings({ ...settings, viewMode: mode })}
                style={{ flex: 1, padding: '15px', borderRadius: '15px', border: settings.viewMode === mode ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)', backgroundColor: settings.viewMode === mode ? 'rgba(59,130,246,0.1)' : '#1f2937', color: 'white', cursor: 'pointer', transition: 'all 0.2s' }}>
                <div style={{ fontSize: '18px', marginBottom: '4px' }}>{mode === 'list' ? '📋' : '🗺️'}</div>
                <div style={{ fontSize: '15px', fontWeight: 'bold' }}>{mode === 'list' ? '목록 형태' : '지도 형태'}</div>
              </button>
            ))}
          </div>
        </section>

        {/* 데이터 및 시스템 */}
        <section>
          <h3 style={{ fontSize: '16px', color: '#3b82f6', marginBottom: '10px', fontWeight: '600' }}>💾 데이터 및 시스템</h3>
          <div style={{ backgroundColor: '#1f2937', padding: '15px', borderRadius: '15px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '14px' }}>기록 내보내기</span>
              <button style={{ backgroundColor: 'transparent', border: '1px solid #3b82f6', color: '#3b82f6', padding: '6px 12px', borderRadius: '8px', fontSize: '12px', cursor: 'pointer' }}>파일 다운로드</button>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '12px' }}>
              <span style={{ fontSize: '14px' }}>연결 상태</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981' }}></div>
                <span style={{ fontSize: '12px', color: '#10b981' }}>정상 (24ms)</span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <button onClick={onClose}
        style={{ width: '100%', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '12px', padding: '14px', fontWeight: 'bold', fontSize: '16px', marginTop: '20px', cursor: 'pointer' }}>
        설정 저장 및 닫기
      </button>
    </div>
  </div>
);

export default SettingsModal;
