import { useState, useEffect } from 'react';

export function useAuth() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState({ name: '방문객', role: 'Guest' });
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [loginInput, setLoginInput] = useState({ id: '', pw: '' });

  // 앱 로드 시 localStorage에서 로그인 상태 복구
  useEffect(() => {
    const savedUser = localStorage.getItem('searchlight_user');
    if (savedUser) {
      const parsedUser = JSON.parse(savedUser);
      setUser(parsedUser);
      setIsLoggedIn(true);
      console.log(`[Auth] 이전 세션 복구 완료: ${parsedUser.name}`);
    }
  }, []);

  const handleLogin = (e) => {
    e.preventDefault();
    if (loginInput.id && loginInput.pw) {
      const newUser = { name: loginInput.id, role: 'Administrator' };
      setUser(newUser);
      setIsLoggedIn(true);
      setShowLoginModal(false);
      setLoginInput({ id: '', pw: '' });
      localStorage.setItem('searchlight_user', JSON.stringify(newUser));
      console.log(`[Auth] 로그인 성공: ${newUser.name}`);
    }
  };

  const executeLogout = () => {
    setIsLoggedIn(false);
    setUser({ name: '방문객', role: 'Guest' });
    setShowLogoutModal(false);
    localStorage.removeItem('searchlight_user');
    console.log('[Auth] 로그아웃 완료');
  };

  return {
    isLoggedIn, user,
    showLoginModal, setShowLoginModal,
    showLogoutModal, setShowLogoutModal,
    loginInput, setLoginInput,
    handleLogin, executeLogout,
  };
}
