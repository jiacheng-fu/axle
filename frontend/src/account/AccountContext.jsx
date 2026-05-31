import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { supabase, isSupabaseConfigured } from "../lib/supabase.js";

const AccountContext = createContext(null);

const carVin = (car) => String(car?.id ?? `${car?.year}-${car?.make}-${car?.model}-${car?.price}`);

export function AccountProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(!isSupabaseConfigured); // if not configured, we're "ready" (no auth)
  const [savedList, setSavedList] = useState([]);   // [carSnapshot, ...]
  const [savedVins, setSavedVins] = useState(() => new Set());

  // Track the auth session.
  useEffect(() => {
    if (!supabase) return;
    let active = true;
    supabase.auth.getSession().then(({ data }) => {
      if (!active) return;
      setUser(data.session?.user ?? null);
      setReady(true);
    });
    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });
    return () => {
      active = false;
      sub?.subscription?.unsubscribe();
    };
  }, []);

  // Load saved cars whenever the user changes.
  const loadSaved = useCallback(async (uid) => {
    if (!supabase || !uid) {
      setSavedList([]);
      setSavedVins(new Set());
      return;
    }
    const { data, error } = await supabase
      .from("saved_vehicles")
      .select("vin, car, created_at")
      .order("created_at", { ascending: false });
    if (error) {
      console.warn("[account] load saved failed:", error.message);
      return;
    }
    setSavedList((data || []).map((r) => r.car));
    setSavedVins(new Set((data || []).map((r) => r.vin)));
  }, []);

  useEffect(() => {
    loadSaved(user?.id);
  }, [user?.id, loadSaved]);

  const signInWithGoogle = useCallback(async () => {
    if (!supabase) return;
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: window.location.origin },
    });
  }, []);

  const signOut = useCallback(async () => {
    if (!supabase) return;
    await supabase.auth.signOut();
    setSavedList([]);
    setSavedVins(new Set());
  }, []);

  const isSaved = useCallback((car) => savedVins.has(carVin(car)), [savedVins]);

  // Toggle a heart. Returns "signin" if the user needs to authenticate first.
  const toggleSave = useCallback(
    async (car) => {
      if (!supabase || !user) return "signin";
      const vin = carVin(car);
      const already = savedVins.has(vin);

      // Optimistic update.
      setSavedVins((prev) => {
        const next = new Set(prev);
        already ? next.delete(vin) : next.add(vin);
        return next;
      });
      setSavedList((prev) =>
        already ? prev.filter((c) => carVin(c) !== vin) : [car, ...prev]
      );

      try {
        if (already) {
          const { error } = await supabase.from("saved_vehicles").delete().eq("vin", vin);
          if (error) throw error;
        } else {
          const { error } = await supabase
            .from("saved_vehicles")
            .upsert({ user_id: user.id, vin, car }, { onConflict: "user_id,vin" });
          if (error) throw error;
        }
        return "ok";
      } catch (e) {
        console.warn("[account] toggleSave failed:", e.message);
        loadSaved(user.id); // re-sync from server on failure
        return "error";
      }
    },
    [user, savedVins, loadSaved]
  );

  const value = useMemo(
    () => ({
      configured: isSupabaseConfigured,
      ready,
      user,
      signInWithGoogle,
      signOut,
      savedList,
      savedCount: savedList.length,
      isSaved,
      toggleSave,
    }),
    [ready, user, signInWithGoogle, signOut, savedList, isSaved, toggleSave]
  );

  return <AccountContext.Provider value={value}>{children}</AccountContext.Provider>;
}

export function useAccount() {
  const ctx = useContext(AccountContext);
  if (!ctx) throw new Error("useAccount must be used within <AccountProvider>");
  return ctx;
}
