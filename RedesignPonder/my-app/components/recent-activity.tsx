"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, CheckCircle, Award, BookOpen, GraduationCap } from "lucide-react"

export function RecentActivity() {
  const activities = [
    {
      id: 1,
      type: "message",
      title: "New feedback from AI Mentor",
      description: "Great progress on your collaborative filtering implementation!",
      time: "2 hours ago",
      icon: MessageSquare,
      color: "from-blue-500 to-cyan-500",
    },
    {
      id: 2,
      type: "completion",
      title: "Task completed",
      description: "Finished 'Understanding Matrix Factorization'",
      time: "5 hours ago",
      icon: CheckCircle,
      color: "from-emerald-500 to-teal-500",
    },
    {
      id: 3,
      type: "achievement",
      title: "Achievement unlocked",
      description: "Earned 'Data Science Fundamentals' badge",
      time: "1 day ago",
      icon: Award,
      color: "from-yellow-500 to-orange-500",
    },
    {
      id: 4,
      type: "submission",
      title: "Project checkpoint submitted",
      description: "Week 1 deliverables for Recommendation Engine",
      time: "2 days ago",
      icon: BookOpen,
      color: "from-purple-500 to-pink-500",
    },
    {
      id: 5,
      type: "milestone",
      title: "Learning milestone reached",
      description: "Completed 50% of Python ML fundamentals",
      time: "3 days ago",
      icon: GraduationCap,
      color: "from-teal-500 to-emerald-500",
    },
  ]

  return (
    <Card className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-teal-600 to-emerald-600 dark:from-teal-400 dark:to-emerald-400 bg-clip-text text-transparent">
          Recent Activity
        </h2>
        <Badge variant="secondary" className="bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300">
          5 new
        </Badge>
      </div>

      <div className="space-y-4">
        {activities.map((activity) => (
          <div
            key={activity.id}
            className="flex items-start gap-4 p-4 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            <div className={`p-2 rounded-lg bg-gradient-to-r ${activity.color}`}>
              <activity.icon className="h-4 w-4 text-white" />
            </div>

            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-gray-900 dark:text-white">{activity.title}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{activity.description}</p>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">{activity.time}</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
