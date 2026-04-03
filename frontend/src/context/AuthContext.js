import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import config from "../config";

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshToken, setRefreshToken] = useState(null);
   const [isAuthenticated, setIsAuthenticated] = useState(false);

  const fetchUserInfo = useCallback(async (token) => {
  try {
    const response = await fetch(`${config.API_BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (response.ok) {
      const userData = await response.json();
      console.log("%%%%%%%%%%%%%5", userData);
      setUser(userData);
      localStorage.setItem("userPhotoUrl", userData?.photo_url);
    } else if (response.status === 401) {
      logout();
    }
  } catch (err) {
    console.error(err);
  } finally {
    setLoading(false); 
  }
}, []);

  React.useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (storedToken) {
      setToken(storedToken);
      fetchUserInfo(storedToken);
    } else {
      setLoading(false);
    }
  }, [fetchUserInfo]);
  const refreshUser = useCallback(async () => {
  if (!token) return;
  await fetchUserInfo(token);
}, [token, fetchUserInfo]);

  const login = async (email, password) => {
    console.log("#######################",email,password)
    const res = await fetch(`${config.API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
      identifier: email, 
      password
    }),
    });
    console.log("%%%%%%%%%%%%%%%%%%%%%%%%%%%%5",res)
    if (!res.ok) {
      console.log("%$$$$$$$$$@@@@@@@@@@@",res)
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Login failed");
    }
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    setToken(data.access_token);
    await fetchUserInfo(data.access_token);
  };

  const register = async (email, password, full_name, username,phone_number,is_email_verified,is_phone_verified) => {
    const res = await fetch(`${config.API_BASE_URL}/auth/register-or-login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        full_name,
        username,
        phone_number,
        is_new_user: true,
        is_email_verified,
        is_phone_verified
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed");
    }

    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    setToken(data.access_token);
    console.log("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!@@@", data.access_token);
    await fetchUserInfo(data.access_token);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };
  
  const sendOtp = async (identifier) => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/auth/send-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: identifier.includes("@") ? identifier : null,
          phone_number: !identifier.includes("@") ? identifier : null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to send OTP");
      }

      return await response.json();
    } catch (error) {
      console.error("Send OTP error:", error);
      throw error;
    }
  };

  const verifyOtp = async (identifier, otp) => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/auth/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: identifier.includes("@") ? identifier : null,
          phone_number: !identifier.includes("@") ? identifier : null,
          otp,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Invalid OTP");
      }

      const data = await response.json();

      // Expecting backend to also return tokens after OTP verification
      if (data.access_token) {
        localStorage.setItem("token", data.access_token);
        if (data.refresh_token) {
          localStorage.setItem("refreshToken", data.refresh_token);
          setRefreshToken(data.refresh_token);
        }
        setToken(data.access_token);
        await fetchUserInfo(data.access_token);
      }

      return data;
    } catch (error) {
      console.error("Verify OTP error:", error);
      throw error;
    }
  };

  const resetPasswordWithOtp = async (identifier, otp, newPassword) => {
    try {
      const response = await fetch(
        `${config.API_BASE_URL}/auth/reset-password-with-otp`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: identifier.includes("@") ? identifier : null,
            phone_number: !identifier.includes("@") ? identifier : null,
            otp,
            new_password: newPassword,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Password reset failed");
      }

      return await response.json();
    } catch (error) {
      console.error("Reset password error:", error);
      throw error;
    }
  };

  const googleLogin = () => {
    return new Promise((resolve, reject) => {
      const apiUrl= `${config.API_BASE_URL}/auth/oauth/google`
      const oauthWindow = window.open(
        apiUrl,
        "googleLogin",
        "width=500,height=600"
      );
      console.log("********************************************************", apiUrl);
      const handleMessage = async (event) => {
        // Accept messages only from backend
        if (event.origin !== config.API_BASE_URL) return;

        const userData = event.data;
        if (userData?.access_token) {
          localStorage.setItem("token", userData.access_token);
          if (userData.refresh_token) {
            localStorage.setItem("refreshToken", userData.refresh_token);
          }
          setToken(userData.access_token);
          await fetchUserInfo(userData.access_token);
          resolve(userData);
        } else {
          reject(new Error("Invalid login response"));
        }
        window.removeEventListener("message", handleMessage);
      };

      window.addEventListener("message", handleMessage);

      setTimeout(() => {
        reject(new Error("Google login timed out"));
        window.removeEventListener("message", handleMessage);
      }, 60000);
    });
  };

const updateProfile = async (formData, file) => {
  console.log("!!!!!!!!!!!!!!!!!!!!!!!!!!!!@@@@",formData,file)
  const data = new FormData();
  Object.keys(formData).forEach((key) => {
    if (formData[key] !== undefined && formData[key] !== null) {
      data.append(key, formData[key].toString());
    }
  });
  if (file) data.append("file", file);

  const response = await fetch(`${config.API_BASE_URL}/auth/me/update`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: data,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Profile update failed");
  }
    
  const updatedUser = await response.json();
  setUser(updatedUser);
  return updatedUser;
};

const profileCompletion = useCallback(async () => {
  try {
    const response = await fetch(`${config.API_BASE_URL}/auth/profile-completion`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.detail || "Profile completion check failed");
    }

    console.log("Profile completion data:", data);
    localStorage.setItem('profileCompletion',data?.completion_percentage || 0);
    return data;
  } catch (error) {
    console.error("Profile completion error:", error);
    throw error;
  }
}, [token]);

const submitEmail = async (user) => {
  console.log("%%%%%%%%%%%%%5",user)
  try {
    const response = await fetch(`${config.API_BASE_URL}/auth/submit-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
       body: JSON.stringify({
        email: user.email,
        name: user.name,
        phone_number: user.phone_number,
        message: user.message,
      }),
    });
console.log("!!!!!!!!!!!!!!!11",response)
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to submit email");
    }

    return await response.json();
  } catch (error) {
    console.error("Submit email error:", error);
    throw error;
  }
};

useEffect(() => {
  if (!token) return;

  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    const expiryTime = payload.exp * 1000;
    const now = Date.now();

    if (expiryTime < now) {
      logout();
    } else {
      const timeout = setTimeout(() => {
        logout();
      }, expiryTime - now);
      return () => clearTimeout(timeout);
    }
  } catch (err) {
    logout();
  }
}, [token, logout]); 
  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!token,
    sendOtp,
    verifyOtp,
    submitEmail,
    resetPasswordWithOtp,
    googleLogin,
    updateProfile,
    profileCompletion,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;