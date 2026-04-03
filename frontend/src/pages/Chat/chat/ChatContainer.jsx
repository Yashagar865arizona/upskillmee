import React, { useState, useEffect, useRef, useCallback } from "react";
import styles from "./ChatContainer.module.css";
import { useLearningPlan } from "../context/LearningPlanContext";
import { useAuth } from "../../../context/AuthContext";
import config from "../../../config";
import AgentModeSelector from "../../../components/Chat/AgentModeSelector";
import robot from "../../../assets/robot.webp";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { getObjByKey } from "../../../utils/storage";
import axios from "axios";
import Delete from "../../../assets/delete.png";
import duolingoIcons from "../../../assets/duolingo";
import Avatar from "../../../assets/avatar.png";
import { useTheme } from "../../../context/ThemeContext";

const SessionIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path
      d="M3 6h14M3 10h14M3 14h14"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
  </svg>
);

const NewSessionIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path
      d="M10 3v14M3 10h14"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
  </svg>
);

const CloseIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <path
      d="M12 4L4 12M4 4l8 8"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
  </svg>
);

const SendIcon = () => (
  <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
    <circle cx="18" cy="18" r="18" fill="#FC8D0B" />
    <path
      d="M12.4843 11.8308C12.2829 11.8022 12.0809 11.8776 11.9474 12.031C11.814 12.1844 11.7673 12.3949 11.8233 12.5903L12.9543 16.531C13.1019 17.0455 13.5724 17.4 14.1077 17.4H19.0001C19.3314 17.4 19.6001 17.6687 19.6001 18C19.6001 18.3314 19.3314 18.6 19.0001 18.6H14.1077C13.5725 18.6 13.1019 18.9545 12.9543 19.469L11.8233 23.4097C11.7673 23.6052 11.814 23.8157 11.9474 23.9691C12.0809 24.1225 12.2829 24.1978 12.4843 24.1693C17.1545 23.5074 21.3768 21.455 24.7187 18.4459C24.8451 18.3321 24.9172 18.1701 24.9172 18C24.9172 17.83 24.8451 17.6679 24.7187 17.5542C21.3768 14.5451 17.1545 12.4927 12.4843 11.8308Z"
      fill="#161340"
    />
  </svg>
);

const BASE_STORAGE_KEY = "upskillmee_chat_messages";
const SESSIONS_STORAGE_KEY = "upskillmee_chat_sessions";
const CONNECTION_STATUS = {
  CONNECTING: "connecting",
  CONNECTED: "connected",
  DISCONNECTED: "disconnected",
  RECONNECTING: "reconnecting",
  ERROR: "error",
};

const generateSessionId = () =>
  `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const getSessionTitle = (messages) => {
  if (!Array.isArray(messages) || messages.length === 0) return "New Chat";
  const firstUserMessage = messages.find(
    (msg) => msg.sender === "user" && msg.text
  );
  if (firstUserMessage)
    return firstUserMessage.text.length > 50
      ? firstUserMessage.text.slice(0, 50) + "..."
      : firstUserMessage.text;
  return "New Chat";
};

const formatSessionDate = (timestamp) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffInHours = (now - date) / (1000 * 60 * 60);

  if (diffInHours < 24)
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  if (diffInHours < 168)
    return date.toLocaleDateString("en-US", {
      weekday: "short",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
};

const groupSessionsByDate = (sessions) => {
  if (!Array.isArray(sessions)) return {};
  const groups = {};
  const now = new Date();

  sessions.forEach((session) => {
    if (!session?.timestamp) return;
    const sessionDate = new Date(session.timestamp);
    const diffInHours = (now - sessionDate) / (1000 * 60 * 60);
    let key;
    if (diffInHours < 24) key = "Today";
    else if (diffInHours < 48) key = "Yesterday";
    else if (diffInHours < 168) key = "This Week";
    else if (diffInHours < 720) key = "This Month";
    else key = "Older";
    groups[key] = groups[key] || [];
    groups[key].push(session);
  });

  Object.keys(groups).forEach((key) =>
    groups[key].sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
  );
  return groups;
};

export const ChatContainer = () => {
const { darkMode} = useTheme();
  const { updateProjects, refreshPlans } = useLearningPlan();
  
  const { user, token } = useAuth();
  const userId = user?.id || "anonymous";
  const STORAGE_KEY = `${BASE_STORAGE_KEY}_${userId}`;
  const USER_SESSIONS_KEY = `${SESSIONS_STORAGE_KEY}_${userId}`;

  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessions, setSessions] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(USER_SESSIONS_KEY)) || [];
      return Array.isArray(saved) ? saved : [];
    } catch {
      return [];
    }
  });
  const [showSessionList, setShowSessionList] = useState(false);
  const [agentMode, setAgentMode] = useState("chat");
  const [availableModes, setAvailableModes] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState(
    CONNECTION_STATUS.DISCONNECTED
  );
  const [messages, setMessages] = useState(() => {
    const savedSessions =
      JSON.parse(localStorage.getItem(USER_SESSIONS_KEY)) || [];
    if (Array.isArray(savedSessions) && savedSessions.length) {
      const recent = savedSessions.sort(
        (a, b) => (b.timestamp || 0) - (a.timestamp || 0)
      )[0];
      setCurrentSessionId(recent.id);
      return Array.isArray(recent.messages) ? recent.messages : [];
    }
    return [
      {
        id: 1,
        text: "Hey! I'm your upskillmee AI Mentor. How can I help you today? 😊",
        sender: "bot",
        avatar: Avatar,
      },   
    ];
  });

  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const heartbeatIntervalRef = useRef(null);

  const chatStarted = messages.some((msg) => msg.sender === "user");

  const scrollToBottom = () =>
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });

  const getAvatarIcon = (message, index) => {
    const keys = Object.keys(duolingoIcons);
    return message.sender === "user"
      ? Avatar
      : duolingoIcons[keys[index % keys.length]];
  };

  const createNewSession = useCallback(() => {
    const newSessionId = generateSessionId();
    const newMessages = [
      {
        id: 1,
        text: "Hey! I'm your upskillmee AI Mentor. How can I help you today? 😊",
        sender: "bot",
        avatar: getAvatarIcon({}, 0),
      },
    ];
    const newSession = {
      id: newSessionId,
      title: "New Chat",
      timestamp: Date.now(),
      messages: newMessages,
      lastActivity: Date.now(),
    };

    setCurrentSessionId(newSessionId);
    setMessages(newMessages);
    setShowSessionList(false);
    setSessions((prev) => {
      const updated = [newSession, ...prev];
      localStorage.setItem(USER_SESSIONS_KEY, JSON.stringify(updated));
      return updated;
    });
  }, [USER_SESSIONS_KEY]);

  const switchToSession = useCallback(
    (sessionId) => {
      const session = sessions.find((s) => s.id === sessionId);
      if (!session) return;
      setCurrentSessionId(sessionId);
      setMessages(session.messages || []);
      setShowSessionList(false);
      setSessions((prev) => {
        const updated = prev.map((s) =>
          s.id === sessionId ? { ...s, lastActivity: Date.now() } : s
        );
        localStorage.setItem(USER_SESSIONS_KEY, JSON.stringify(updated));
        return updated;
      });
    },
    [sessions, USER_SESSIONS_KEY]
  );

  const handleDeleteSession = (sessionId) => {
    if (!window.confirm("Are you sure you want to delete this session?"))
      return;
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    if (sessionId === currentSessionId) createNewSession();
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const token = getObjByKey("loginResponse")?.access_token;
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post(
        `${config.API_BASE_URL}/documents/upload`,
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      console.log("Upload success:", res.data);
    } catch (err) {
      console.error("Upload failed:", err.response?.data || err.message);
    }
  };

  useEffect(() => scrollToBottom(), [messages]);

  useEffect(() => {
    if (!currentSessionId && messages.length > 0) createNewSession();
  }, [currentSessionId, messages, createNewSession]);

  useEffect(() => {
    if (!currentSessionId) return;
    const updatedSessions = [...sessions];
    const index = updatedSessions.findIndex((s) => s.id === currentSessionId);
    const title = getSessionTitle(messages);

    if (index >= 0)
      updatedSessions[index] = {
        ...updatedSessions[index],
        title,
        messages,
        lastActivity: Date.now(),
      };
    else
      updatedSessions.unshift({
        id: currentSessionId,
        title,
        messages,
        timestamp: Date.now(),
        lastActivity: Date.now(),
      });

    localStorage.setItem(USER_SESSIONS_KEY, JSON.stringify(updatedSessions));
    setSessions(updatedSessions);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages, currentSessionId, STORAGE_KEY, sessions]);

  const handleWebSocketMessage = useCallback((event) => {
    try {
      const data = JSON.parse(event.data);
      if (
        !data ||
        data.status ||
        data.type === "heartbeat_ack" ||
        data.type === "system"
      )
        return;

      if (data.agent_info?.available_modes)
        setAvailableModes(data.agent_info.available_modes);
      if (data.error) return;

      const messageContent = data.text || data.content || "";
      if (!messageContent.trim()) return;
      const isLearningPlan = !!data.learning_plan;

      setMessages((prev) => [
        ...prev,
        {
          id: data.id || Date.now(),
          text: messageContent,
          sender: "bot",
          avatar: getAvatarIcon({}, prev.length),
          isLearningPlan: !!data.learning_plan,
        },
      ]);
      if (isLearningPlan) {
        refreshPlans();
      }
    } catch (err) {
      console.error("WebSocket message error:", err);
    }
  }, [refreshPlans]);

  const connectWebSocket = useCallback(
    (initialDelay = 0) => {
      if (reconnectTimeoutRef.current)
        clearTimeout(reconnectTimeoutRef.current);

      setTimeout(() => {
        try {
          wsRef.current?.close();
          setConnectionStatus(CONNECTION_STATUS.CONNECTING);

          let wsUrl = `${config.WS_BASE_URL}/chat/ws`;
          if (
            window.location.protocol === "https:" &&
            wsUrl.startsWith("ws://")
          )
            wsUrl = wsUrl.replace("ws://", "wss://");

          wsRef.current = new WebSocket(wsUrl);

          wsRef.current.onopen = () => {
            reconnectAttemptsRef.current = 0;
            setConnectionStatus(CONNECTION_STATUS.CONNECTED);
            setTimeout(() => {
              wsRef.current?.send(JSON.stringify({ type: "auth", token }));
              heartbeatIntervalRef.current = setInterval(() => {
                if (wsRef.current?.readyState === WebSocket.OPEN)
                  wsRef.current.send(JSON.stringify({ type: "heartbeat" }));
                else clearInterval(heartbeatIntervalRef.current);
              }, 30000);
            }, 500);
          };

          wsRef.current.onmessage = handleWebSocketMessage;

          wsRef.current.onclose = (event) => {
            clearInterval(heartbeatIntervalRef.current);
            setConnectionStatus(CONNECTION_STATUS.DISCONNECTED);
            if (!event.wasClean && reconnectAttemptsRef.current < 5) {
              reconnectAttemptsRef.current++;
              const delay = Math.min(
                1000 * 2 ** reconnectAttemptsRef.current,
                30000
              );
              setConnectionStatus(CONNECTION_STATUS.RECONNECTING);
              reconnectTimeoutRef.current = setTimeout(
                () => connectWebSocket(delay),
                delay
              );
            } else if (reconnectAttemptsRef.current >= 5)
              setConnectionStatus(CONNECTION_STATUS.ERROR);
          };

          wsRef.current.onerror = (error) => {
            console.error("WebSocket error:", error);
            setConnectionStatus(CONNECTION_STATUS.ERROR);
          };
        } catch (err) {
          console.error("WebSocket connection failed:", err);
          setConnectionStatus(CONNECTION_STATUS.ERROR);
        }
      }, initialDelay);
    },
    [handleWebSocketMessage, token]
  );

  useEffect(() => {
    if (!token) return;
    connectWebSocket();
    return () => {
      wsRef.current?.close();
      clearInterval(heartbeatIntervalRef.current);
      clearTimeout(reconnectTimeoutRef.current);
    };
  }, [token, connectWebSocket]);

  const sendMessage = useCallback(
    (message) => {
      if (!message.trim()) return;
      const userMessage = { id: Date.now(), text: message, sender: "user" };
      setMessages((prev) => [...prev, userMessage]);

      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            message,
            agent_mode: agentMode,
            token,
            chat_history: messages,
          })
        );
      } else {
        setConnectionStatus(CONNECTION_STATUS.RECONNECTING);
        connectWebSocket();
      }
    },
    [agentMode, connectWebSocket, messages, token]
  );

  if (!token) return <div>Please log in to access the chat.</div>;

  return (
    <div
      className={`${styles.chatContainer} ${darkMode ? styles.dark : styles.light}`}
    >
      <div className={styles.sessionHeader}>
        <div className={styles.sessionControls}>
          <button
            className={styles.sessionListButton}
            onClick={() => setShowSessionList(!showSessionList)}
            title="Session History"
          >
            <SessionIcon />
            <span>{getSessionTitle(messages)}</span>
          </button>
          <button
            className={styles.newSessionButton}
            onClick={createNewSession}
            title="New Chat"
          >
            <NewSessionIcon />
          </button>
        </div>
      </div>

      {showSessionList && (
        <div className={styles.sessionListOverlay}>
          <div className={styles.sessionList}>
            <div className={styles.sessionListHeader}>
              <h3>Chat Sessions</h3>
              <button
                className={styles.closeSessionList}
                onClick={() => setShowSessionList(false)}
              >
                <CloseIcon />
              </button>
            </div>
            <div className={styles.sessionListContent}>
              {Object.entries(groupSessionsByDate(sessions)).map(
                ([group, groupSessions]) => (
                  <div key={group} className={styles.sessionGroup}>
                    <div className={styles.sessionGroupTitle}>{group}</div>
                    {groupSessions.map((session) => (
                      <div
                        key={session.id}
                        className={`${styles.sessionItem} ${
                          session.id === currentSessionId
                            ? styles.activeSession
                            : ""
                        }`}
                        onClick={() => switchToSession(session.id)}
                      >
                        <div className={styles.sessionTitle}>
                          {session.title}
                        </div>
                        <div className={styles.sessionDate}>
                          {formatSessionDate(session.timestamp)}
                        </div>
                        <button
                          className={styles.deleteButton}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteSession(session.id);
                          }}
                        >
                          <img
                            src={Delete}
                            alt="Delete"
                            width={16}
                            height={16}
                          />
                        </button>
                      </div>
                    ))}
                  </div>
                )
              )}
              {!sessions.length && (
                <div className={styles.noSessions}>
                  No previous chats. Start a new conversation!
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {connectionStatus !== CONNECTION_STATUS.CONNECTED && (
        <div
          className={`${styles.connectionStatus} ${styles[connectionStatus]}`}
        >
          {connectionStatus === CONNECTION_STATUS.CONNECTING &&
            "🔄 Connecting..."}
          {connectionStatus === CONNECTION_STATUS.RECONNECTING &&
            "🔄 Reconnecting..."}
          {connectionStatus === CONNECTION_STATUS.ERROR &&
            "❌ Connection Error"}
        </div>
      )}

      <div className={styles.messageList}>
        {!chatStarted && (
          <div className={styles.welcomeAnimation}>
            <img src={robot} alt="Welcome" className={styles.botImage} />
            <p className={styles.welcomeText}>
              Hey! I'm your upskillmee AI Mentor. How can I help you today? 😊
            </p>
          </div>
        )}

        {chatStarted &&
          messages.map((message, idx) => (
            <div
              key={message.id}
              className={`${styles.messageWrapper} ${
                message.sender === "user"
                  ? styles.userMessage
                  : styles.botMessage
              } ${message.isLearningPlan ? styles.learningPlanMessage : ""}`}
            >
              <div className={styles.avatarContainer}>
                <img
                  src={message.avatar || getAvatarIcon(message, idx)}
                  alt={message.sender === "user" ? "User" : "Bot"}
                  className={styles.avatar}
                />
              </div>
              <div className={styles.messageContent}>
                {message.isLearningPlan && (
                  <div className={styles.learningPlanBadge}>
                    🎯 Learning Plan
                  </div>
                )}
                <ReactMarkdown
                  children={message.text}
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeRaw]}
                  components={{
                    h1: (props) => (
                      <h1 className="text-2xl font-bold mt-3 mb-2" {...props} />
                    ),
                    h2: (props) => (
                      <h2
                        className="text-xl font-semibold mt-3 mb-1"
                        {...props}
                      />
                    ),
                    p: (props) => (
                      <p
                        className="text-base leading-relaxed my-2"
                        {...props}
                      />
                    ),
                    li: (props) => (
                      <li className="ml-4 my-1 list-decimal" {...props} />
                    ),
                    ul: (props) => (
                      <ul
                        className="list-disc ml-6 my-2 space-y-1"
                        {...props}
                      />
                    ),
                    ol: (props) => (
                      <ol
                        className="list-decimal ml-6 my-2 space-y-1"
                        {...props}
                      />
                    ),
                  }}
                />
              </div>
            </div>
          ))}
        <div ref={messagesEndRef} />
      </div>

      <div className={styles.inputWrapper}>
        <form
          className={styles.inputContainer}
          onSubmit={(e) => {
            e.preventDefault();
            const message = e.target.message.value.trim();
            if (!message) return;
            sendMessage(message);
            e.target.message.value = "";
          }}
        >
          <div className={styles.agentModeWrapper}>
            <AgentModeSelector
              currentMode={agentMode}
              onModeChange={setAgentMode}
              availableModes={availableModes}
            />
          </div>
          <div className={styles.inputWithExtras}>
            <label htmlFor="file-upload" className={styles.uploadButton}>
              <input
                type="file"
                id="file-upload"
                style={{ display: "none" }}
                onChange={handleFileUpload}
              />
              🧷
            </label>
            <input
              type="text"
              name="message"
              placeholder="Type a message..."
              className={styles.messageInput}
            />
            <button
              type="submit"
              className={styles.sendButton}
              aria-label="Send message"
              onClick={(e) => e.stopPropagation()}
            >
              <SendIcon />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
