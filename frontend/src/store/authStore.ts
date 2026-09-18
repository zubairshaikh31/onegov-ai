"use client";
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { User } from "@/types/auth";

interface AuthStore {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  setLoading: (loading: boolean) => void;
  clearAuth: () => void;
}

const checkIsAdmin = (user: User | null): boolean => {
  if (!user || !user.roles) return false;
  return user.roles.some((r) => r.name === "admin");
};

const setAuthCookies = (isLoggedIn: boolean, isAdmin: boolean) => {
  if (typeof document === "undefined") return;
  if (isLoggedIn) {
    document.cookie = "onegov-logged-in=true; path=/; max-age=604800; SameSite=Lax";
    document.cookie = `onegov-role=${isAdmin ? "admin" : "user"}; path=/; max-age=604800; SameSite=Lax`;
  } else {
    document.cookie = "onegov-logged-in=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie = "onegov-role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  }
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isAdmin: false,
      isLoading: false,
      setAuth: (user, accessToken, refreshToken) => {
        const isAdmin = checkIsAdmin(user);
        setAuthCookies(true, isAdmin);
        set({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
          isAdmin,
        });
      },
      setTokens: (accessToken, refreshToken) => {
        const currentUser = get().user;
        const isAdmin = checkIsAdmin(currentUser);
        setAuthCookies(true, isAdmin);
        set({ accessToken, refreshToken, isAuthenticated: true });
      },
      setUser: (user) => {
        const isAdmin = checkIsAdmin(user);
        setAuthCookies(true, isAdmin);
        set({ user, isAdmin });
      },
      setLoading: (isLoading) => set({ isLoading }),
      clearAuth: () => {
        setAuthCookies(false, false);
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isAdmin: false,
          isLoading: false,
        });
      },
    }),
    {
      name: "onegov-auth",
      storage: createJSONStorage(() => {
        if (typeof window === "undefined")
          return { getItem: () => null, setItem: () => {}, removeItem: () => {} };
        return localStorage;
      }),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        isAdmin: state.isAdmin,
      }),
      merge: (persistedState: any, currentState) => {
        const merged = {
          ...currentState,
          ...(persistedState as object),
        };
        // Preserving active in-memory accessToken if present
        if (currentState.accessToken) {
          merged.accessToken = currentState.accessToken;
        }
        return merged;
      },
    },
  ),
);

