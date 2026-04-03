"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Award, Trophy, Star, Target } from "lucide-react"

export function Achievements() {
  const achievements = [
    {
      id: 1,
      title: "First Steps",
      description: "Complete your first learning task",
      icon: Star,
      earned: true,
      earnedDate: "2 weeks ago",
      color: "from-yellow-500 to-orange-500",
    },
    {
      id: 2,
      title: "Data Science Fundamentals",
      description: "Master the basics of data science",
      icon: Award,
      earned: true,
      earnedDate: "1 week ago",
      color: "from-blue-500 to-cyan-500",
    },
    {
      id: 3,
      title: "Streak Master",
      description: "Maintain a 7-day learning streak",
      icon: Trophy,
      earned: true,
      earnedDate: "3 days ago",
      color: "from-emerald-500 to-teal-500",
    },
  ]

  const nextAchievement = {
    title: "ML Expert",
    description: "Complete 3 machine learning projects",
    progress: 33,
    current: 1,
    target: 3,
  }

  return (
    <Card className="p-6">
      <h2 className="text-xl font-bold bg-gradient-to-r from-teal-600 to-emerald-600 dark:from-teal-400 dark:to-emerald-400 bg-clip-text text-transparent mb-6">
        Achievements
      </h2>

      {/* Earned Badges */}
      <div className="space-y-3 mb-6">
        {achievements.map((achievement) => (
          <div key={achievement.id} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
            <div className={`p-2 rounded-lg bg-gradient-to-r ${achievement.color}`}>
              <achievement.icon className="h-4 w-4 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-900 dark:text-white text-sm">{achievement.title}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{achievement.earnedDate}</p>
            </div>
            <Badge className="bg-gradient-to-r from-teal-500 to-emerald-500 text-white text-xs">Earned</Badge>
          </div>
        ))}
      </div>

      {/* Next Achievement */}
      <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
        <h3 className="font-medium text-gray-900 dark:text-white mb-3">Next Achievement</h3>
        <div className="p-4 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500">
              <Target className="h-4 w-4 text-white" />
            </div>
            <div className="flex-1">
              <p className="font-medium text-gray-900 dark:text-white text-sm">{nextAchievement.title}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{nextAchievement.description}</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400">Progress</span>
              <span className="text-gray-600 dark:text-gray-400">
                {nextAchievement.current}/{nextAchievement.target}
              </span>
            </div>
            <Progress
              value={nextAchievement.progress}
              className="h-2 bg-gray-200 dark:bg-gray-700 [&>div]:bg-gradient-to-r [&>div]:from-purple-500 [&>div]:to-pink-500"
            />
          </div>
        </div>
      </div>
    </Card>
  )
}
