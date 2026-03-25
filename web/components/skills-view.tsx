
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Zap, Code, Terminal, Search, PenTool, GitBranch } from "lucide-react";

interface Skill {
  name: string;
  description: string;
  category: string;
}

interface SkillsViewProps {
  skills: Skill[];
}

const categoryIcons: Record<string, any> = {
  development: Code,
  system: Terminal,
  research: Search,
  writing: PenTool,
  general: Zap,
};

const categoryColors: Record<string, string> = {
  development: "default",
  system: "accent",
  research: "secondary",
  writing: "muted",
  general: "default",
};

export function SkillsView({ skills }: SkillsViewProps) {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-lc-text">Skills</h1>
        <p className="text-sm text-lc-muted mt-1">
          Built-in and custom skills available to the agent
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {skills.map((skill) => {
          const Icon = categoryIcons[skill.category] || Zap;
          return (
            <Card key={skill.name} className="hover:border-lc-muted/40 transition-colors">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-lc-primary/10 flex items-center justify-center">
                      <Icon className="w-4 h-4 text-lc-primary" />
                    </div>
                    <CardTitle className="text-base">{skill.name}</CardTitle>
                  </div>
                  <Badge variant={(categoryColors[skill.category] as any) || "default"}>
                    {skill.category}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-lc-muted">{skill.description}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
