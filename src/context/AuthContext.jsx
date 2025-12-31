import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { getSupabaseClient, isSupabaseConfigured } from "../utils/supabaseClient.js";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(isSupabaseConfigured);

  useEffect(() => {
    if (!isSupabaseConfigured) {
      setLoading(false);
      return undefined;
    }

    let isActive = true;
    let unsubscribe = null;

    const bootstrapSession = async () => {
      const supabase = await getSupabaseClient();
      if (!supabase || !isActive) {
        return;
      }

      const {
        data: { session: currentSession },
      } = await supabase.auth.getSession();

      if (isActive) {
        setSession(currentSession);
        setLoading(false);
      }
      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange((_, nextSession) => {
        if (isActive) {
          setSession(nextSession);
          setLoading(false);
        }
      });
      unsubscribe = () => subscription.unsubscribe();
    };

    bootstrapSession();

    return () => {
      isActive = false;
      unsubscribe?.();
    };
  }, []);

  const value = useMemo(
    () => ({
      isConfigured: isSupabaseConfigured,
      loading,
      session,
      user: session?.user || null,
      accessToken: session?.access_token || null,
      async signInWithOtp(email) {
        const supabase = await getSupabaseClient();
        if (!supabase) {
          throw new Error("Supabase auth is not configured.");
        }

        const { error } = await supabase.auth.signInWithOtp({
          email,
          options: {
            emailRedirectTo: `${window.location.origin}/saved-trips`,
          },
        });
        if (error) {
          throw error;
        }
      },
      async signInWithGoogle() {
        const supabase = await getSupabaseClient();
        if (!supabase) {
          throw new Error("Supabase auth is not configured.");
        }

        const { error } = await supabase.auth.signInWithOAuth({
          provider: "google",
          options: {
            redirectTo: `${window.location.origin}/saved-trips`,
          },
        });
        if (error) {
          throw error;
        }
      },
      async signOut() {
        const supabase = await getSupabaseClient();
        if (!supabase) {
          return;
        }
        const { error } = await supabase.auth.signOut();
        if (error) {
          throw error;
        }
      },
    }),
    [loading, session]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return context;
};
