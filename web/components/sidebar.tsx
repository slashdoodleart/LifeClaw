"use client";

import { useState } from "react";
import {
  MessageSquare,
  Settings,
  Palette,
  Puzzle,
  Server,
  Zap,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const tabs = [
  { id: "chat", icon: MessageSquare, label: "Chat" },
  { id: "skills", icon: Zap, label: "Skills" },
  { id: "mcp", icon: Server, label: "MCP" },
  { id: "themes", icon: Palette, label: "Themes" },
  { id: "settings", icon: Settings, label: "Settings" },
];

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div
      className={cn(
        "flex flex-col border-r border-lc-muted/20 bg-lc-surface/50 backdrop-blur-sm transition-all duration-300",
        collapsed ? "w-16" : "w-56"
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 p-4 border-b border-lc-muted/20">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-lc-primary to-lc-secondary flex items-center justify-center text-lc-bg font-bold text-sm">
          LC
        </div>
        {!collapsed && (
          <span className="font-bold text-lc-text tracking-tight">LifeClaw</span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 p-2 space-y-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200",
                isActive
                  ? "bg-lc-primary/15 text-lc-primary font-medium"
                  : "text-lc-muted hover:text-lc-text hover:bg-lc-muted/10"
              )}
            >
              <Icon size={18} />
              {!collapsed && <span>{tab.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="p-3 border-t border-lc-muted/20 text-lc-muted hover:text-lc-text transition-colors"
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </div>
  );
}
