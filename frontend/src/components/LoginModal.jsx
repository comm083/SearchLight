import React, { useState } from 'react';
import { Shield, Mail, Lock, X } from 'lucide-react';

const ACCOUNTS = {
  admin:    { name: '관리자',   role: '관리자' },
  operator: { name: '관제요원', role: '관제요원' },
};

const LoginModal = ({ onClose, onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const account = ACCOUNTS[email];
    if (account && password === '1234') {
      onLogin(account.name, account.role);
      onClose();
    } else {
      setError('아이디 또는 비밀번호가 일치하지 않습니다.');
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} style={{ zIndex: 1000 }}>
      <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px', padding: '30px', borderRadius: '16px', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '40px', height: '40px', backgroundColor: 'rgba(59,130,246,0.1)', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(59,130,246,0.2)' }}>
              <Shield size={24} color="#3b82f6" />
            </div>
            <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '700', color: '#f9fafb' }}>SearchLight</h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9ca3af', padding: '4px' }}>
            <X size={20} />
          </button>
        </div>

        <p style={{ color: '#6b7280', fontSize: '14px', marginBottom: '24px', fontWeight: '400' }}>보안 분석관 계정으로 로그인해주세요.</p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '13px', color: '#4b5563', marginBottom: '8px', fontWeight: '500' }}>아이디</label>
            <div style={{ position: 'relative' }}>
              <Mail size={18} color="#9ca3af" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                className="modal-input"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="admin 또는 operator"
                style={{ paddingLeft: '42px', width: '100%', boxSizing: 'border-box', marginBottom: '0', height: '44px', borderRadius: '8px' }}
                autoFocus
              />
            </div>
          </div>
          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '13px', color: '#4b5563', marginBottom: '8px', fontWeight: '500' }}>비밀번호</label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} color="#9ca3af" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="password"
                className="modal-input"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="****"
                style={{ paddingLeft: '42px', width: '100%', boxSizing: 'border-box', marginBottom: '0', height: '44px', borderRadius: '8px' }}
              />
            </div>
          </div>

          {/* 역할 안내 */}
          <div style={{ marginBottom: '20px', backgroundColor: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.15)', borderRadius: '8px', padding: '12px 14px', fontSize: '12px', color: '#6b7280', lineHeight: '1.6' }}>
            <span style={{ color: '#60a5fa', fontWeight: '600' }}>관리자</span> — 다운로드·삭제 포함 전체 권한<br />
            <span style={{ color: '#9ca3af', fontWeight: '600' }}>관제요원</span> — 조회·영상 재생만 가능
          </div>

          {error && (
            <div style={{ color: '#ef4444', fontSize: '13px', marginBottom: '16px', backgroundColor: '#fef2f2', padding: '10px', borderRadius: '6px', border: '1px solid #fee2e2' }}>
              {error}
            </div>
          )}

          <button type="submit" className="modal-btn confirm" style={{ width: '100%', height: '44px', fontSize: '15px', fontWeight: '600', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', transition: 'background-color 0.2s' }}>
            로그인
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginModal;
