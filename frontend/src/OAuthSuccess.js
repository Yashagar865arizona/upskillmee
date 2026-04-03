import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";

const OAuthSuccess = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { fetchUserInfo } = useAuth();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const token = params.get("token");

    if (token) {
      localStorage.setItem("token", token);
      fetchUserInfo(token)
        .then(() => navigate("/dashboard", { replace: true }))
        .catch((err) => {
          console.error("OAuth fetchUserInfo failed:", err);
          navigate("/auth/login", { replace: true });
        });
    } else {
      navigate("/auth/login", { replace: true });
    }
  }, [location, navigate, fetchUserInfo]);

  return <div>Logging you in...</div>;
};

export default OAuthSuccess;
