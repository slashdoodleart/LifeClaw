"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Sidebar } from "@/components/sidebar";
import { ChatView } from "@/components/chat-view";
import { ThemesView } from "@/components/themes-view";
import { SkillsView } from "@/components/skills-view";
import { MCPView } from "@/components/mcp-view";
import { SettingsView } from "@/components/settings-view";
import { applyTheme } from "@/lib/themes";
import { LifeClawSocket } from "@/lib/websocket";

// Default skills (before server sends real ones)
const defaultSkills = [
  { name: "coder", description: "Expert coding assistant", category: "development" },
  { name: "shell", description: "System administration expert", category: "system" },
  { name: "researcher", description: "Research and analyze information", category: "research" },
  { name: "writer", description: "Technical writing assistant", category: "writing" },
  { name: "git-expert", description: "Git workflow assistant", category: "development" },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState("chat");
  const [currentTheme, setCurrentTheme] = useState("aurora");
  const [connected, setConnected] = useState(false);
  const [skills, setSkills] = useState(defaultSkills);
  const [mcpServers, setMCPServers] = useState<string[]>([]);
  const [config, setConfig] = useState({
    model: "ollama/llama3.2",
    provider: "ollama",
    theme: "aurora",
    mcpCount: 0,
  });

  const socketRef = useRef<LifeClawSocket | null>(null);
  const pendingResolve = useRef<((value: string) => void) | null>(null);

  useEffect(() => {
    applyTheme(currentTheme);
  }, [currentTheme]);

  useEffect(() => {
    const socket = new LifeClawSocket();
    socketRef.current = socket;

    socket.on("connected", () => setConnected(true));
    socket.on("disconnected", () => setConnected(false));

    socket.on("init", (msg: any) => {
      const data = msg.data;
      if (data.theme) {
        setCurrentTheme(data.theme);
        applyTheme(data.theme);
      }
      if (data.model) setConfig((prev) => ({ ...prev, model: data.model }));
      if (data.provider) setConfig((prev) => ({ ...prev, provider: data.provider }));
      if (data.mcp_servers) {
        setMCPServers(data.mcp_servers);
        setConfig((prev) => ({ ...prev, mcpCount: data.mcp_servers.length }));
      }
    });

    socket.on("response", (msg: any) => {
      if (pendingResolve.current) {
        pendingResolve.current(msg.content || "");
        pendingResolve.current = null;
      }
    });

    socket.on("skills", (msg: any) => {
      if (msg.data) setSkills(msg.data);
    });

    socket.on("theme_changed", (msg: any) => {
      setCurrentTheme(msg.theme);
      applyTheme(msg.theme);
    });

    socket.connect();

    return () => socket.disconnect();
  }, []);

  const handleSend = useCallback(async (message: string): Promise<string> => {
    return new Promise((resolve) => {
      pendingResolve.current = resolve;
      socketRef.current?.send("chat", { content: message });

      // Timeout after 2 minutes
      setTimeout(() => {
        if (pendingResolve.current === resolve) {
          pendingResolve.current = null;
          resolve("Request timed out. Check the terminal for details.");
        }
      }, 120000);
    });
  }, []);

  const handleThemeChange = (slug: string) => {
    setCurrentTheme(slug);
    applyTheme(slug);
    setConfig((prev) => ({ ...prev, theme: slug }));
    socketRef.current?.send("set_theme", { theme: slug });
  };

  return (
    <div className="flex h-screen bg-lc-bg">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="flex-1 overflow-hidden">
        {activeTab === "chat" && <ChatView onSend={handleSend} connected={connected} />}
        {activeTab === "themes" && (
          <ThemesView currentTheme={currentTheme} onThemeChange={handleThemeChange} />
        )}
        {activeTab === "skills" && <SkillsView skills={skills} />}
        {activeTab === "mcp" && <MCPView servers={mcpServers} />}
        {activeTab === "settings" && <SettingsView config={config} />}
      </main>
    </div>
  );
}
