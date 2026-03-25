
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Settings, Cpu, Globe, Thermometer } from "lucide-react";

interface SettingsViewProps {
  config: {
    model: string;
    provider: string;
    theme: string;
    mcpCount: number;
  };
}

export function SettingsView({ config }: SettingsViewProps) {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-lc-text">Settings</h1>
        <p className="text-sm text-lc-muted mt-1">Configure LifeClaw</p>
      </div>

      <div className="space-y-4">
        {/* Model */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-lc-primary" />
              <CardTitle className="text-base">Model</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <p className="text-sm text-lc-text font-medium">{config.model}</p>
                <p className="text-xs text-lc-muted">Provider: {config.provider}</p>
              </div>
              <Badge>{config.provider}</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4 text-lc-secondary" />
              <CardTitle className="text-base">Status</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-lc-bg rounded-lg p-3">
                <p className="text-xs text-lc-muted">Theme</p>
                <p className="text-sm font-medium text-lc-text">{config.theme}</p>
              </div>
              <div className="bg-lc-bg rounded-lg p-3">
                <p className="text-xs text-lc-muted">MCP Servers</p>
                <p className="text-sm font-medium text-lc-text">{config.mcpCount}</p>
              </div>
              <div className="bg-lc-bg rounded-lg p-3">
                <p className="text-xs text-lc-muted">Provider</p>
                <p className="text-sm font-medium text-lc-text">{config.provider}</p>
              </div>
              <div className="bg-lc-bg rounded-lg p-3">
                <p className="text-xs text-lc-muted">Version</p>
                <p className="text-sm font-medium text-lc-text">0.1.0</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Config File */}
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-lc-accent" />
              <CardTitle className="text-base">Configuration</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-lc-muted">
              Edit configuration at <code className="bg-lc-bg px-1.5 py-0.5 rounded text-lc-accent text-xs">~/.lifeclaw/config.json</code>
            </p>
            <p className="text-sm text-lc-muted mt-2">
              Or run <code className="bg-lc-bg px-1.5 py-0.5 rounded text-lc-accent text-xs">lifeclaw setup</code> for the interactive wizard.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
