"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Play, BookOpen, Clock } from "lucide-react"

export function LearningProgress() {
  const learningPlans = [
    {
      id: 1,
      title: "Build a Recommendation Engine",
      description: "Machine Learning with Python",
      progress: 65,
      currentWeek: 2,
      totalWeeks: 4,
      tasksCompleted: 8,
      totalTasks: 12,
      timeSpent: "24h 30m",
      status: "active",
    },
    {
      id: 2,
      title: "Full-Stack Web Development",
      description: "React & Node.js Project",
      progress: 30,
      currentWeek: 1,
      totalWeeks: 6,
      tasksCompleted: 3,
      totalTasks: 18,
      timeSpent: "12h 15m",
      status: "paused",
    },
  ]

  return (
    <Card className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-teal-600 to-emerald-600 dark:from-teal-400 dark:to-emerald-400 bg-clip-text text-transparent">
          Learning Progress
        </h2>
        <Button variant="outline" size="sm">
          View All Plans
        </Button>
      </div>

      <div className="space-y-6">
        {learningPlans.map((plan) => (
          <div
            key={plan.id}
            className={`p-6 rounded-xl border-2 transition-all duration-300 ${
              plan.status === "active"
                ? "bg-gradient-to-br from-teal-50 to-emerald-50 dark:from-teal-950 dark:to-emerald-950 border-teal-200 dark:border-teal-800"
                : "bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700"
            }`}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{plan.title}</h3>
                  <Badge
                    className={
                      plan.status === "active"
                        ? "bg-gradient-to-r from-teal-500 to-emerald-500 text-white"
                        : "bg-gray-500 text-white"
                    }
                  >
                    {plan.status}
                  </Badge>
                </div>
                <p className="text-gray-600 dark:text-gray-400 mb-4">{plan.description}</p>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Overall Progress</span>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{plan.progress}%</span>
                  </div>
                  <Progress
                    value={plan.progress}
                    className="h-3 bg-gray-200 dark:bg-gray-700 [&>div]:bg-gradient-to-r [&>div]:from-teal-500 [&>div]:to-emerald-500"
                  />
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="flex items-center gap-2">
                    <BookOpen className="h-4 w-4 text-teal-500" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      Week {plan.currentWeek}/{plan.totalWeeks}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Play className="h-4 w-4 text-emerald-500" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {plan.tasksCompleted}/{plan.totalTasks} tasks
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-cyan-500" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">{plan.timeSpent}</span>
                  </div>
                </div>
              </div>

              <Button
                className={
                  plan.status === "active"
                    ? "bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 text-white"
                    : "bg-gray-500 hover:bg-gray-600 text-white"
                }
              >
                {plan.status === "active" ? "Continue Learning" : "Resume"}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
