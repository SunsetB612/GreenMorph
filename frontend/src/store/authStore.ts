/**
 * 认证状态管理
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// API基础URL
// const API_BASE_URL = 'http://localhost:8000/api';
const API_BASE_URL = import.meta.env.VITE_API_URL;
// 类型定义
interface User {
  id: number;
  username: string;
  email: string;
  bio?: string;
  skill_level: string;
  points: number;
  is_active: boolean;
  created_at: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

interface AuthStore extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      // Actions
      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      login: async (credentials: LoginRequest) => {
        set({ isLoading: true });
        try {
          const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials),
          });

          if (!response.ok) {
            let errorMessage = '登录失败';
            try {
              const errorData = await response.json();
              console.log('后端错误响应:', errorData);
              errorMessage = errorData.detail || errorMessage;
              console.log('提取的错误信息:', errorMessage);
            } catch (parseError) {
              console.error('解析错误响应失败:', parseError);
              errorMessage = `登录失败 (${response.status})`;
            }
            console.log('抛出错误:', errorMessage);
            throw new Error(errorMessage);
          }

          const data = await response.json();
          
          // 保存token到localStorage
          localStorage.setItem('auth_token', data.access_token);
          
          set({
            user: data.user,
            token: data.access_token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          console.error('登录错误:', error);
          // 只重置isLoading状态，不触发其他状态更新
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (userData: RegisterRequest) => {
        set({ isLoading: true });
        try {
          const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData),
          });

          if (!response.ok) {
            let errorMessage = '注册失败';
            try {
              const errorData = await response.json();
              console.log('后端错误响应:', errorData);
              errorMessage = errorData.detail || errorMessage;
              console.log('提取的错误信息:', errorMessage);
            } catch (parseError) {
              console.error('解析错误响应失败:', parseError);
              errorMessage = `注册失败 (${response.status})`;
            }
            console.log('抛出错误:', errorMessage);
            throw new Error(errorMessage);
          }

          const data = await response.json();
          
          // 注册成功后自动登录
          await get().login({
            email: userData.email,
            password: userData.password,
          });
        } catch (error) {
          console.error('注册错误:', error);
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        localStorage.removeItem('auth_token');
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });
      },

      checkAuth: async () => {
        const token = localStorage.getItem('auth_token');
        if (!token) {
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
          return;
        }

        set({ isLoading: true });
        try {
          const response = await fetch(`${API_BASE_URL}/auth/me`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });

          if (!response.ok) {
            // Token无效，清除本地存储
            localStorage.removeItem('auth_token');
            set({
              user: null,
              token: null,
              isAuthenticated: false,
              isLoading: false,
            });
            return;
          }

          const user = await response.json();
          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          console.error('验证认证状态失败:', error);
          localStorage.removeItem('auth_token');
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
