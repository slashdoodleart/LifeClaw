"use client";

import { themes, type ThemeColors } from "@/lib/themes";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";

interface ThemesViewProps {
  currentTheme: string;
  onThemeChange: (slug: string) => void;
}

export function ThemesView({ currentTheme, onThemeChange }: ThemesViewProps) {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-lc-text">Themes</h1>
        <p className="text-sm text-lc-muted mt-1">Choose your visual style</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(themes).map(([slug, theme]) => {
          const isActive = slug === currentTheme;
          return (
            <button
              key={slug}
              onClick={() => onThemeChange(slug)}
              className="text-left group"
            >
              <Card
                className={`transition-all duration-200 hover:scale-[1.02] ${
                  isActive ? "ring-2 ring-lc-primary" : "hover:border-lc-muted/40"
                }`}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{theme.name}</CardTitle>
                    {isActive && (
                      <div className="w-6 h-6 rounded-full bg-lc-primary flex items-center justify-center">
                        <Check className="w-3.5 h-3.5 text-lc-bg" />
                      </div>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {/* Color preview */}
                  <div className="flex gap-2 mb-3">
                    {[theme.primary, theme.secondary, theme.accent].map((color, i) => (
                      <div
                        key={i}
                        className="w-8 h-8 rounded-lg shadow-inner"
                        style={{ backgroundColor: color }}
                      />
                    ))}
                    <div
                      className="flex-1 h-8 rounded-lg shadow-inner"
                      style={{ backgroundColor: theme.bg }}
                    />
                  </div>

                  {/* Preview bar */}
                  <div
                    className="rounded-lg p-3 space-y-2"
                    style={{ backgroundColor: theme.bg }}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: theme.primary }}
                      />
                      <div
                        className="h-2 w-20 rounded"
                        style={{ backgroundColor: theme.surface }}
                      />
                    </div>
                    <div
                      className="h-2 w-full rounded"
                      style={{ backgroundColor: theme.surface }}
                    />
                    <div
                      className="h-2 w-3/4 rounded"
                      style={{ backgroundColor: theme.muted }}
                    />
                  </div>
                </CardContent>
              </Card>
            </button>
          );
        })}
      </div>
    </div>
  );
}
