"use client"

import { memo } from "react"
import { TrendingUp, Clock, Target, Zap } from 'lucide-react'

export const StatsGrid = memo(function StatsGrid() {
  const stats = [
    {
      label: "Learning Streak",
      value: "15",
      unit: "days",
      change: "Keep it up!",
      icon: Zap,
      color: "from-orange-500 to-red-500",
      bg: "from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20",
      border: "border-orange-200 dark:border-orange-800",
    },
    {
      label: "Hours This Week",
      value: "12.5",
      unit: "hrs",
      change: "Great pace!",
      icon: Clock,
      color: "from-blue-500 to-cyan-500",
      bg: "from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20",
      border: "border-blue-200 dark:border-blue-800",
    },
    {
      label: "Skills Mastered",
      value: "8",
      unit: "skills",
      change: "Amazing progress!",
      icon: Target,
      color: "from-green-500 to-emerald-500",
      bg: "from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20",
      border: "border-green-200 dark:border-green-800",
    },
    {
      label: "Progress Rate",
      value: "94",
      unit: "%",
      change: "Excellent!",
      icon: TrendingUp,
      color: "from-teal-500 to-blue-500",
      bg: "from-teal-50 to-blue-50 dark:from-teal-900/20 dark:to-blue-900/20",
      border: "border-teal-200 dark:border-teal-800",
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className={`p-5 bg-gradient-to-br ${stat.bg} rounded-lg border ${stat.border} hover:shadow-md transition-all duration-300 hover:scale-105`}
        >
          <div className="flex items-start justify-between mb-3">
            <div className={`p-2.5 rounded-md bg-gradient-to-r ${stat.color} shadow-sm`}>
              <stat.icon className="h-4 w-4 text-white" />
            </div>
          </div>

          <div className="space-y-0.5">
            <div className="flex items-baseline gap-1">
              <span className="text-xl font-bold text-gray-900 dark:text-white">{stat.value}</span>
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">{stat.unit}</span>
            </div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{stat.label}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">{stat.change}</p>
          </div>
        </div>
      ))}
    </div>
  )
})
