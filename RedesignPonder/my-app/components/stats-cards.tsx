"use client"

import { memo } from "react"
import { Card } from "@/components/ui/card"
import { Flame, Target, Trophy } from "lucide-react"

export const StatsCards = memo(function StatsCards() {
  const stats = [
    {
      icon: Flame,
      title: "Learning Streak",
      value: "15 Days",
      color: "from-orange-500 to-red-500",
      bgColor: "from-orange-50 to-red-50 dark:from-orange-950 dark:to-red-950",
    },
    {
      icon: Target,
      title: "Current Progress",
      value: "Week 2",
      color: "from-teal-500 to-emerald-500",
      bgColor: "from-teal-50 to-emerald-50 dark:from-teal-950 dark:to-emerald-950",
    },
    {
      icon: Trophy,
      title: "Achievements",
      value: "8 Earned",
      color: "from-yellow-500 to-orange-500",
      bgColor: "from-yellow-50 to-orange-50 dark:from-yellow-950 dark:to-orange-950",
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {stats.map((stat) => (
        <Card key={stat.title} className={`p-6 bg-gradient-to-br ${stat.bgColor}`}>
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl bg-gradient-to-br ${stat.color}`}>
              <stat.icon className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">{stat.title}</p>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
})
