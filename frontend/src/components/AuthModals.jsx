import React from 'react';
import { Lock, LogOut } from 'lucide-react';

export const LoginModal = ({ loginInput, setLoginInput, onLogin, onClose }) => (
  <div className="modal-overlay" style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(5px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
    <div className="modal-content" style={{ backgroundColor: '#111827', padding: '40px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)', width: '350px' }}>
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
        <div style={{ padding: '15px', backgroundColor: '#3b82f6', borderRadius: '15px' }}><Lock size={32} /></div>
      </div>
      <h2 style={{ textAlign: 'center', marginBottom: '10px', fontSize: '20px' }}>시스템 관리자 인증</h2>
      <p style={{ textAlign: 'center', color: '#6b7280', fontSize: '12px', marginBottom: '30px' }}>계정 정보를 입력해 주세요.</p>
      <form onSubmit={onLogin}>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '5px', display: 'block' }}>ID</label>
          <input type="text" required value={loginInput.id} onChange={(e) => setLoginInput({ ...loginInput, id: e.target.value })}
            style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '12px', color: 'white' }} placeholder="관리자 아이디" />
        </div>
        <div style={{ marginBottom: '30px' }}>
          <label style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '5px', display: 'block' }}>PASSWORD</label>
          <input type="password" required value={loginInput.pw} onChange={(e) => setLoginInput({ ...loginInput, pw: e.target.value })}
            style={{ width: '100%', backgroundColor: '#1f2937', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '12px', color: 'white' }} placeholder="••••••••" />
        </div>
        <button type="submit" style={{ width: '100%', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '10px', padding: '14px', fontWeight: 'bold', cursor: 'pointer' }}>인증 및 로그인</button>
        <button type="button" onClick={onClose} style={{ width: '100%', background: 'transparent', color: '#6b7280', border: 'none', marginTop: '15px', fontSize: '12px', cursor: 'pointer' }}>닫기</button>
      </form>
    </div>
  </div>
);

export const LogoutModal = ({ onConfirm, onClose }) => (
  <div className="modal-overlay" style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(5px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
    <div className="modal-content" style={{ backgroundColor: '#111827', padding: '40px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)', width: '350px', textAlign: 'center' }}>
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
        <div style={{ padding: '15px', backgroundColor: '#ef4444', borderRadius: '15px' }}><LogOut size={32} /></div>
      </div>
      <h2 style={{ marginBottom: '10px', fontSize: '20px' }}>로그아웃</h2>
      <p style={{ color: '#6b7280', fontSize: '12px', marginBottom: '30px' }}>정말 시스템에서 로그아웃 하시겠습니까?</p>
      <div style={{ display: 'flex', gap: '10px' }}>
        <button onClick={onConfirm} style={{ flex: 1, backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '10px', padding: '14px', fontWeight: 'bold', cursor: 'pointer' }}>로그아웃</button>
        <button onClick={onClose} style={{ flex: 1, backgroundColor: '#1f2937', color: 'white', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', padding: '14px', fontWeight: 'bold', cursor: 'pointer' }}>취소</button>
      </div>
    </div>
  </div>
);
