"use client"

import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Clock, Target, BookOpen } from "lucide-react"

export function AnalyticsSnapshot() {
  const stats = [
    {
      label: "This Week",
      value: "12h 30m",
      change: "+2h from last week",
      positive: true,
      icon: Clock,
    },
    {
      label: "Skills Developed",
      value: "8",
      change: "+3 from last month",
      positive: true,
      icon: Target,
    },
    {
      label: "Projects Completed",
      value: "2",
      change: "Same as last month",
      positive: null,
      icon: BookOpen,
    },
  ]

  const weeklyProgress = [
    { day: "Mon", hours: 2.5 },
    { day: "Tue", hours: 1.8 },
    { day: "Wed", hours: 3.2 },
    { day: "Thu", hours: 2.1 },
    { day: "Fri", hours: 1.9 },
    { day: "Sat", hours: 0.8 },
    { day: "Sun", hours: 0.2 },
  ]

  const maxHours = Math.max(...weeklyProgress.map((d) => d.hours))

  return (
    <Card className="p-6">
      <h2 className="text-xl font-bold bg-gradient-to-r from-teal-600 to-emerald-600 dark:from-teal-400 dark:to-emerald-400 bg-clip-text text-transparent mb-6">
        Analytics Snapshot
      </h2>

      {/* Key Stats */}
      <div className="space-y-4 mb-6">
        {stats.map((stat) => (
          <div key={stat.label} className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-r from-teal-500 to-emerald-500">
              <stat.icon className="h-4 w-4 text-white" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</span>
                <span className="font-semibold text-gray-900 dark:text-white">{stat.value}</span>
              </div>
              <p
                className={`text-xs ${
                  stat.positive === true
                    ? "text-emerald-600 dark:text-emerald-400"
                    : stat.positive === false
                      ? "text-red-600 dark:text-red-400"
                      : "text-gray-500 dark:text-gray-400"
                }`}
              >
                {stat.change}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Weekly Chart */}
      <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
        <h3 className="font-medium text-gray-900 dark:text-white mb-4 text-sm">This Week's Activity</h3>
        <div className="space-y-3">
          {weeklyProgress.map((day) => (
            <div key={day.day} className="flex items-center gap-3">
              <span className="text-xs text-gray-500 dark:text-gray-400 w-8">{day.day}</span>
              <div className="flex-1">
                <Progress
                  value={(day.hours / maxHours) * 100}
                  className="h-2 bg-gray-200 dark:bg-gray-700 [&>div]:bg-gradient-to-r [&>div]:from-teal-500 [&>div]:to-emerald-500"
                />
              </div>
              <span className="text-xs text-gray-600 dark:text-gray-400 w-8">{day.hours}h</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}
