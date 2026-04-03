"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Lightbulb, TrendingUp, BookOpen, Clock } from "lucide-react"

export function InsightsRecommendations() {
  const recommendations = [
    {
      id: 1,
      type: "skill",
      title: "Focus on Deep Learning",
      description: "Based on your ML progress, dive deeper into neural networks",
      icon: TrendingUp,
      color: "from-blue-500 to-cyan-500",
      action: "Explore Path",
    },
    {
      id: 2,
      type: "project",
      title: "Build a Chatbot",
      description: "Perfect next project to apply your NLP knowledge",
      icon: Lightbulb,
      color: "from-emerald-500 to-teal-500",
      action: "Start Project",
    },
    {
      id: 3,
      type: "resource",
      title: "Advanced Python Patterns",
      description: "Recommended reading for this week",
      icon: BookOpen,
      color: "from-purple-500 to-pink-500",
      action: "Read Now",
    },
  ]

  const todayInsight = {
    title: "Peak Learning Time",
    description: "You're most productive between 9-11 AM",
    icon: Clock,
    tip: "Schedule challenging tasks during this window",
  }

  return (
    <Card className="p-6">
      <h2 className="text-xl font-bold bg-gradient-to-r from-teal-600 to-emerald-600 dark:from-teal-400 dark:to-emerald-400 bg-clip-text text-transparent mb-6">
        Insights & Recommendations
      </h2>

      {/* Today's Insight */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-teal-50 to-emerald-50 dark:from-teal-950 dark:to-emerald-950 border border-teal-200 dark:border-teal-800 mb-6">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-r from-teal-500 to-emerald-500">
            <todayInsight.icon className="h-4 w-4 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-gray-900 dark:text-white text-sm mb-1">{todayInsight.title}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{todayInsight.description}</p>
            <p className="text-xs text-teal-700 dark:text-teal-300 font-medium">{todayInsight.tip}</p>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="space-y-4">
        {recommendations.map((rec) => (
          <div
            key={rec.id}
            className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start gap-3 mb-3">
              <div className={`p-2 rounded-lg bg-gradient-to-r ${rec.color}`}>
                <rec.icon className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-medium text-gray-900 dark:text-white text-sm">{rec.title}</h3>
                  <Badge variant="secondary" className="text-xs">
                    {rec.type}
                  </Badge>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">{rec.description}</p>
              </div>
            </div>
            <Button size="sm" variant="outline" className="w-full bg-transparent">
              {rec.action}
            </Button>
          </div>
        ))}
      </div>
    </Card>
  )
}
