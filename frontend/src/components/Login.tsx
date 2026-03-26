import React, { useState } from 'react';
import { useAuthStore } from '../store/useAuthStore';
import { Lock, User } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { setToken } = useAuthStore();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      });

      if (!res.ok) {
        throw new Error('Invalid username or password');
      }

      const data = await res.json();
      setToken(data.access_token);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md glass rounded-2xl p-8 border border-white/[0.06] shadow-2xl relative overflow-hidden">
        {/* Decorative blobez */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-accent-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />
        
        <div className="relative z-10">
          <div className="text-center mb-10">
            <h1 className="text-3xl font-bold tracking-tight text-white mb-2">BillForge</h1>
            <p className="text-slate-400">Sign in to your account</p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm font-medium text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-4">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-slate-500" />
                </div>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="block w-full pl-11 pr-4 py-3 bg-surface-900/50 border border-white/[0.06] rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-transparent transition-all"
                  placeholder="Username"
                />
              </div>

              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-slate-500" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-11 pr-4 py-3 bg-surface-900/50 border border-white/[0.06] rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-accent-500/50 focus:border-transparent transition-all"
                  placeholder="Password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-3.5 px-4 rounded-xl text-sm font-semibold text-white bg-accent-600 hover:bg-accent-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-surface-950 focus:ring-accent-500 disabled:opacity-50 transition-all shadow-lg shadow-accent-500/20"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
          
          <div className="mt-8 text-center">
            <p className="text-xs text-slate-500">
              Wave 1 SaaS Hardening • Secure Authentication
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
