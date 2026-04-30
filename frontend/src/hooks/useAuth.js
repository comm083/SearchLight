import { useState, useEffect } from 'react';

export const useAuth = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState({ name: '방문객', role: 'Guest' });

  useEffect(() => {
    const savedUser = localStorage.getItem('searchlight_user');
    if (savedUser) {
      const parsedUser = JSON.parse(savedUser);
      setUser(parsedUser);
      setIsLoggedIn(true);
    }
  }, []);

  const login = (id, role = 'Administrator') => {
    const newUser = { name: id, role };
    setUser(newUser);
    setIsLoggedIn(true);
    localStorage.setItem('searchlight_user', JSON.stringify(newUser));
  };

  const logout = () => {
    setIsLoggedIn(false);
    setUser({ name: '방문객', role: 'Guest' });
    localStorage.removeItem('searchlight_user');
  };

  return { isLoggedIn, user, login, logout };
};
