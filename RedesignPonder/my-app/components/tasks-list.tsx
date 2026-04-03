"use client"

import { memo } from "react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Calendar, AlertTriangle, ArrowRight, CheckCircle2 } from 'lucide-react'

export const TasksList = memo(function TasksList() {
  const tasks = [
    {
      id: 1,
      title: "Complete collaborative filtering implementation",
      project: "Recommendation Engine",
      dueDate: "Today",
      priority: "high",
      completed: false,
      overdue: false,
      emoji: "🤖",
    },
    {
      id: 2,
      title: "Review matrix factorization concepts",
      project: "Recommendation Engine",
      dueDate: "Tomorrow",
      priority: "medium",
      completed: false,
      overdue: false,
      emoji: "📊",
    },
    {
      id: 3,
      title: "Submit project checkpoint",
      project: "Web Development",
      dueDate: "2 days ago",
      priority: "high",
      completed: false,
      overdue: true,
      emoji: "🚨",
    },
    {
      id: 4,
      title: "Practice Python algorithms",
      project: "Coding Skills",
      dueDate: "This week",
      priority: "low",
      completed: true,
      overdue: false,
      emoji: "🐍",
    },
  ]

  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Learning Tasks</h2>
          <p className="text-gray-600 dark:text-gray-400 text-sm">Stay on track with your goals</p>
        </div>
        <Button variant="ghost" className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300">
          View all <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>

      <div className="space-y-4">
        {tasks.map((task) => (
          <div
            key={task.id}
            className={`p-4 rounded-lg border transition-all duration-300 hover:shadow-md ${
              task.overdue
                ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
                : task.completed
                  ? "bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 opacity-75"
                  : "bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700"
            }`}
          >
            <div className="flex items-start gap-4">
              <Checkbox
                checked={task.completed}
                className="mt-1 data-[state=checked]:bg-teal-500 data-[state=checked]:border-teal-500"
              />

              <div className="flex-1 min-w-0">
                <h3
                  className={`font-medium text-base mb-1 ${
                    task.completed
                      ? "text-gray-500 dark:text-gray-400 line-through"
                      : "text-gray-900 dark:text-white"
                  }`}
                >
                  {task.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{task.project}</p>

                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    {task.overdue ? (
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                    ) : (
                      <Calendar className="h-4 w-4 text-gray-400" />
                    )}
                    <span
                      className={`text-sm font-medium ${
                        task.overdue ? "text-red-600 dark:text-red-400" : "text-gray-500 dark:text-gray-400"
                      }`}
                    >
                      {task.dueDate}
                    </span>
                  </div>

                  <div
                    className={`px-2.5 py-1 rounded-full text-xs font-medium border ${
                      task.priority === "high"
                        ? "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800"
                        : task.priority === "medium"
                          ? "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800"
                          : "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800"
                    }`}
                  >
                    {task.priority}
                  </div>
                </div>
              </div>

              {!task.completed && (
                <Button variant="ghost" size="sm" className="hover:bg-gray-100 dark:hover:bg-gray-700">
                  Start
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
})
