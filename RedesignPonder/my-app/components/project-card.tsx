"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Progress } from "@/components/ui/progress"
import { Lock, CheckCircle2, Play } from 'lucide-react'

interface Task {
  id: string
  text: string
  completed: boolean
}

interface Phase {
  id: string
  week: number
  title: string
  description: string
  tasks: Task[]
  skills: string[]
  status: "completed" | "in-progress" | "locked"
  progress: number
}

interface ProjectCardProps {
  phase: Phase
  isLast: boolean
}

export function ProjectCard({ phase, isLast }: ProjectCardProps) {
  const [tasks, setTasks] = useState(phase.tasks)

  const toggleTask = (taskId: string) => {
    setTasks((prev) => prev.map((task) => (task.id === taskId ? { ...task, completed: !task.completed } : task)))
  }

  const completedTasks = tasks.filter((task) => task.completed).length
  const progress = (completedTasks / tasks.length) * 100

  const getStatusIcon = () => {
    switch (phase.status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-emerald-600" />
      case "in-progress":
        return <Play className="h-5 w-5 text-teal-600" />
      case "locked":
        return <Lock className="h-5 w-5 text-gray-400" />
    }
  }

  const getCardStyles = () => {
    switch (phase.status) {
      case "completed":
        return "bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800 shadow-sm"
      case "in-progress":
        return "bg-teal-50 dark:bg-teal-950/20 border-teal-200 dark:border-teal-800 ring-2 ring-teal-100 dark:ring-teal-900 shadow-md"
      case "locked":
        return "bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 opacity-60"
    }
  }

  return (
    <div className="relative">
      {/* Timeline dot with gradient */}
      <div className="absolute left-0 top-6 w-10 h-10 bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-700 rounded-lg flex items-center justify-center z-10 shadow-sm">
        {getStatusIcon()}
      </div>

      <Card className={`ml-14 p-5 rounded-lg transition-all duration-300 hover:shadow-md ${getCardStyles()}`}>
        <div className="space-y-4">
          {/* Header */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 px-2.5 py-0.5 rounded-full border border-gray-200 dark:border-gray-700">
                Week {phase.week}
              </span>
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white text-base mb-1.5">{phase.title}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{phase.description}</p>
          </div>

          {/* Tasks */}
          {phase.status !== "locked" && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-teal-600 dark:text-teal-400">
                Learning Tasks
              </h4>
              <div className="space-y-2">
                {tasks.map((task) => (
                  <div key={task.id} className="flex items-start gap-3 group">
                    <Checkbox
                      id={task.id}
                      checked={task.completed}
                      onCheckedChange={() => toggleTask(task.id)}
                      className="mt-0.5 data-[state=checked]:bg-teal-500 data-[state=checked]:border-teal-500"
                    />
                    <label
                      htmlFor={task.id}
                      className={`text-sm leading-relaxed cursor-pointer transition-colors ${
                        task.completed
                          ? "text-gray-500 dark:text-gray-400 line-through"
                          : "text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white"
                      }`}
                    >
                      {task.text}
                    </label>
                  </div>
                ))}
              </div>

              {/* Progress with gradient */}
              <div className="pt-2">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Progress</span>
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                    {completedTasks}/{tasks.length}
                  </span>
                </div>
                <Progress
                  value={progress}
                  className="h-1.5 bg-gray-200 dark:bg-gray-700 [&>div]:bg-gradient-to-r [&>div]:from-teal-500 [&>div]:to-emerald-500"
                />
              </div>
            </div>
          )}

          {/* Skills */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Skills You'll Master</h4>
            <div className="flex flex-wrap gap-1.5">
              {phase.skills.map((skill, index) => (
                <Badge
                  key={skill}
                  variant="secondary"
                  className={`text-xs px-2 py-0.5 ${
                    index % 4 === 0
                      ? "bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/20 dark:text-teal-300 dark:border-teal-800"
                      : index % 4 === 1
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/20 dark:text-emerald-300 dark:border-emerald-800"
                        : index % 4 === 2
                          ? "bg-cyan-50 text-cyan-700 border-cyan-200 dark:bg-cyan-950/20 dark:text-cyan-300 dark:border-cyan-800"
                          : "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/20 dark:text-blue-300 dark:border-blue-800"
                  }`}
                >
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
