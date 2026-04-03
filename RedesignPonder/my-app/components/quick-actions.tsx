"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { MessageSquare, Plus, BarChart3, Settings, BookOpen, Target } from "lucide-react"

export function QuickActions() {
  const actions = [
    {
      icon: MessageSquare,
      label: "Start New Chat",
      description: "Ask your AI mentor anything",
      color: "from-blue-500 to-cyan-500",
    },
    {
      icon: Plus,
      label: "New Project",
      description: "Begin a learning journey",
      color: "from-teal-500 to-emerald-500",
    },
    {
      icon: BookOpen,
      label: "Browse Catalog",
      description: "Explore learning paths",
      color: "from-purple-500 to-pink-500",
    },
    {
      icon: BarChart3,
      label: "View Analytics",
      description: "Track your progress",
      color: "from-emerald-500 to-teal-500",
    },
    {
      icon: Target,
      label: "Set Goals",
      description: "Define learning objectives",
      color: "from-orange-500 to-red-500",
    },
    {
      icon: Settings,
      label: "Settings",
      description: "Customize your experience",
      color: "from-gray-500 to-gray-600",
    },
  ]

  return (
    <Card className="p-6">
      <h2 className="text-xl font-bold bg-gradient-to-r from-teal-600 to-emerald-600 dark:from-teal-400 dark:to-emerald-400 bg-clip-text text-transparent mb-6">
        Quick Actions
      </h2>

      <div className="grid grid-cols-1 gap-3">
        {actions.map((action) => (
          <Button
            key={action.label}
            variant="ghost"
            className="h-auto p-4 justify-start text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-all duration-300"
          >
            <div className="flex items-center gap-3 w-full">
              <div className={`p-2 rounded-lg bg-gradient-to-r ${action.color} flex-shrink-0`}>
                <action.icon className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 dark:text-white">{action.label}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{action.description}</p>
              </div>
            </div>
          </Button>
        ))}
      </div>
    </Card>
  )
}
