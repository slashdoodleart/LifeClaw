"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Server, CheckCircle, XCircle } from "lucide-react";

interface MCPViewProps {
  servers: string[];
}

export function MCPView({ servers }: MCPViewProps) {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-lc-text">MCP Servers</h1>
        <p className="text-sm text-lc-muted mt-1">
          Model Context Protocol servers providing tools to the agent
        </p>
      </div>

      {servers.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Server className="w-12 h-12 mx-auto text-lc-muted mb-3" />
            <p className="text-lc-muted">No MCP servers configured</p>
            <p className="text-xs text-lc-muted mt-1">
              Run <code className="bg-lc-surface px-1.5 py-0.5 rounded text-lc-accent">lifeclaw setup</code> to import from Claude Code
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {servers.map((name) => (
            <Card key={name} className="hover:border-lc-muted/40 transition-colors">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-lc-accent/10 flex items-center justify-center">
                      <Server className="w-4 h-4 text-lc-accent" />
                    </div>
                    <CardTitle className="text-base">{name}</CardTitle>
                  </div>
                  <Badge variant="accent">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    active
                  </Badge>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
