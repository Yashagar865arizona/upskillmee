"use client"

import { memo } from "react"
import { MessageSquare, CheckCircle, Award, BookOpen, Sparkles } from 'lucide-react'

export const ActivityFeed = memo(function ActivityFeed() {
  const activities = [
    {
      id: 1,
      type: "message",
      title: "New feedback received",
      description: "Great progress on collaborative filtering!",
      time: "2h ago",
      icon: MessageSquare,
      gradient: "from-blue-500 to-blue-600",
    },
    {
      id: 2,
      type: "completion",
      title: "Task completed",
      description: "Matrix Factorization concepts mastered!",
      time: "5h ago",
      icon: CheckCircle,
      gradient: "from-green-500 to-green-600",
    },
    {
      id: 3,
      type: "achievement",
      title: "Achievement unlocked",
      description: "Data Science Fundamentals badge earned!",
      time: "1d ago",
      icon: Award,
      gradient: "from-yellow-500 to-yellow-600",
    },
    {
      id: 4,
      type: "submission",
      title: "Checkpoint submitted",
      description: "Week 1 deliverables completed successfully!",
      time: "2d ago",
      icon: BookOpen,
      gradient: "from-teal-500 to-teal-600",
    },
    {
      id: 5,
      type: "milestone",
      title: "Learning milestone",
      description: "50% of Python ML fundamentals completed!",
      time: "3d ago",
      icon: Sparkles,
      gradient: "from-teal-500 to-blue-500",
    },
  ]

  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm h-fit">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-1">
          Recent Activity
        </h2>
        <p className="text-gray-500 dark:text-gray-400 text-sm">Your learning highlights</p>
      </div>

      <div className="space-y-4">
        {activities.map((activity, index) => (
          <div key={activity.id} className="relative">
            {index !== activities.length - 1 && (
              <div className="absolute left-5 top-10 w-px h-4 bg-gray-200 dark:bg-gray-700"></div>
            )}

            <div className="flex gap-3 p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200">
              <div
                className={`w-9 h-9 rounded-md bg-gradient-to-r ${activity.gradient} flex items-center justify-center flex-shrink-0`}
              >
                <activity.icon className="h-4 w-4 text-white" />
              </div>

              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-gray-900 dark:text-white text-sm mb-1">
                  {activity.title}
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-300 mb-1">
                  {activity.description}
                </p>
                <p className="text-xs text-gray-400 dark:text-gray-500">{activity.time}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
})
