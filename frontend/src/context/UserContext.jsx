import React, { createContext, useContext, useState, useEffect } from "react";
import config from "../config";
import { useAuth } from "./AuthContext";

const UserContext = createContext();

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) throw new Error("useUser must be used within UserProvider");
  return context;
};

export const UserProvider = ({ children }) => {
  const { token, refreshUser } = useAuth();
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("upskillmee_user");
    return savedUser ? JSON.parse(savedUser) : null;
  });

  useEffect(() => {
    if (user) localStorage.setItem("upskillmee_user", JSON.stringify(user));
    else localStorage.removeItem("upskillmee_user");
  }, [user]);

  const updateUser = (userData) => setUser(userData);

  const logout = () => {
    setUser(null);
    localStorage.removeItem("upskillmee_user");
    localStorage.removeItem("token");
  };

  const submitOnboarding = async (formData) => {
    if (!token) throw new Error("No token found");
    console.log("%%%$$$",formData)
    try {
      const res = await fetch(`${config.API_BASE_URL}/users/onboarding`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      const result = await res.json();
      if (!res.ok)
        throw new Error(result.detail || "Failed to save onboarding");

      updateUser({ ...user, profile: result });
      return result;
    } catch (err) {
      console.error("Onboarding error:", err);
      throw err;
    }
  };
  const fetchQuestions = async () => {
    if (!token) throw new Error("No token found");
    try {
      const res = await fetch(`${config.API_BASE_URL}/users/questions`, {
        method: "GET",
        headers: { Authorization: `Bearer ${token}` },
      });

      const result = await res.json();
      if (!res.ok)
        throw new Error(result.detail || "Failed to fetch questions");

      return result; 
    } catch (err) {
      console.error("Fetch questions error:", err);
      throw err;
    }
  };

  const submitResponses = async (responses) => {
    if (!token) throw new Error("No token found");
    try {
      const res = await fetch(`${config.API_BASE_URL}/users/submit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(responses),
      });

      const result = await res.json();
      await refreshUser();
      if (!res.ok)
        throw new Error(result.detail || "Failed to submit responses");
      return result;
    } catch (err) {
      console.error("Submit responses error:", err);
      throw err;
    }
  };

  return (
    <UserContext.Provider
      value={{
        user,
        updateUser,
        logout,
        submitOnboarding,
        fetchQuestions,
        submitResponses,
      }}
    >
      {children}
    </UserContext.Provider>
  );
};
