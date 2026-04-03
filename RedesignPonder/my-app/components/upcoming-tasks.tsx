"use client"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Calendar, AlertCircle } from "lucide-react"

export function UpcomingTasks() {
  const tasks = [
    {
      id: 1,
      title: "Complete collaborative filtering implementation",
      project: "Recommendation Engine",
      dueDate: "Today",
      priority: "high",
      completed: false,
      overdue: false,
    },
    {
      id: 2,
      title: "Review matrix factorization concepts",
      project: "Recommendation Engine",
      dueDate: "Tomorrow",
      priority: "medium",
      completed: false,
      overdue: false,
    },
    {
      id: 3,
      title: "Submit week 1 project checkpoint",
      project: "Web Development",
      dueDate: "2 days ago",
      priority: "high",
      completed: false,
      overdue: true,
    },
    {
      id: 4,
      title: "Read about content-based filtering",
      project: "Recommendation Engine",
      dueDate: "This week",
      priority: "low",
      completed: true,
      overdue: false,
    },
  ]

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300"
      case "medium":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300"
      case "low":
        return "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300"
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300"
    }
  }

  return (
    <Card className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-teal-600 to-emerald-600 dark:from-teal-400 dark:to-emerald-400 bg-clip-text text-transparent">
          Upcoming Tasks
        </h2>
        <Button variant="outline" size="sm">
          View All Tasks
        </Button>
      </div>

      <div className="space-y-4">
        {tasks.map((task) => (
          <div
            key={task.id}
            className={`p-4 rounded-xl border transition-all duration-300 ${
              task.overdue
                ? "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800"
                : task.completed
                  ? "bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 opacity-60"
                  : "bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 hover:shadow-md"
            }`}
          >
            <div className="flex items-start gap-4">
              <Checkbox
                checked={task.completed}
                className="mt-1 data-[state=checked]:bg-gradient-to-r data-[state=checked]:from-teal-500 data-[state=checked]:to-emerald-500 data-[state=checked]:border-teal-500"
              />

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h3
                      className={`font-medium ${
                        task.completed
                          ? "text-gray-500 dark:text-gray-400 line-through"
                          : "text-gray-900 dark:text-white"
                      }`}
                    >
                      {task.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{task.project}</p>

                    <div className="flex items-center gap-4 mt-3">
                      <div className="flex items-center gap-1">
                        {task.overdue ? (
                          <AlertCircle className="h-4 w-4 text-red-500" />
                        ) : (
                          <Calendar className="h-4 w-4 text-gray-400" />
                        )}
                        <span
                          className={`text-sm ${
                            task.overdue
                              ? "text-red-600 dark:text-red-400 font-medium"
                              : "text-gray-500 dark:text-gray-400"
                          }`}
                        >
                          {task.dueDate}
                        </span>
                      </div>

                      <Badge className={getPriorityColor(task.priority)}>{task.priority}</Badge>
                    </div>
                  </div>

                  {!task.completed && (
                    <Button size="sm" variant="outline">
                      Go to Task
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
