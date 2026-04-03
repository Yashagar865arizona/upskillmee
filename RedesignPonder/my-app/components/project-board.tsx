"use client"

import { memo } from "react"
import { Progress } from "@/components/ui/progress"
import { Checkbox } from "@/components/ui/checkbox"
import { BookOpen, Lock, CheckCircle2, Play } from 'lucide-react'

export const ProjectBoard = memo(function ProjectBoard() {
  const phases = [
    {
      id: "1",
      week: 1,
      title: "Foundations & Setup",
      description: "Environment setup and data exploration",
      tasks: [
        { id: "1-1", text: "Install Python environment", completed: true },
        { id: "1-2", text: "Explore MovieLens dataset", completed: true },
        { id: "1-3", text: "Data preprocessing pipeline", completed: false },
        { id: "1-4", text: "Visualization dashboard", completed: false },
      ],
      skills: ["Python", "Pandas", "Jupyter"],
      status: "in-progress" as const,
      progress: 50,
    },
    {
      id: "2",
      week: 2,
      title: "Collaborative Filtering",
      description: "User and item-based filtering algorithms",
      tasks: [
        { id: "2-1", text: "CF theory understanding", completed: false },
        { id: "2-2", text: "User-based implementation", completed: false },
        { id: "2-3", text: "Item-based implementation", completed: false },
        { id: "2-4", text: "Evaluation and comparison", completed: false },
      ],
      skills: ["Scikit-learn", "Matrix Factorization"],
      status: "locked" as const,
      progress: 0,
    },
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-emerald-500" />
      case "in-progress":
        return <Play className="h-5 w-5 text-teal-500" />
      case "locked":
        return <Lock className="h-5 w-5 text-gray-400" />
    }
  }

  return (
    <div className="h-full bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden shadow-sm">
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center shadow-sm">
            <BookOpen className="h-5 w-5 text-white" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Learning Path
          </h2>
        </div>
        <p className="text-gray-500 dark:text-gray-400 text-sm">Recommendation Engine Project</p>
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-6">
          {phases.map((phase, index) => (
            <div key={phase.id} className="relative">
              {/* Timeline line */}
              {index !== phases.length - 1 && (
                <div className="absolute left-5 top-14 w-px h-12 bg-gray-200 dark:bg-gray-700"></div>
              )}

              {/* Timeline dot */}
              <div className="absolute left-0 top-4 w-10 h-10 bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-700 rounded-lg flex items-center justify-center shadow-sm">
                {getStatusIcon(phase.status)}
              </div>

              <div className="ml-14">
                <div
                  className={`p-4 rounded-lg border transition-all ${
                    phase.status === "in-progress"
                      ? "bg-teal-50 dark:bg-teal-900/20 border-teal-200 dark:border-teal-800"
                      : phase.status === "completed"
                        ? "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800"
                        : "bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 opacity-60"
                  }`}
                >
                  <div className="space-y-3">
                    {/* Header */}
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="px-2 py-0.5 bg-white dark:bg-gray-800 rounded-md text-xs font-medium text-teal-600 dark:text-teal-400">
                          Week {phase.week}
                        </span>
                      </div>
                      <h3 className="font-bold text-gray-900 dark:text-white text-base mb-1">
                        {phase.title}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{phase.description}</p>
                    </div>

                    {/* Tasks */}
                    {phase.status !== "locked" && (
                      <div className="space-y-2">
                        {phase.tasks.map((task) => (
                          <div key={task.id} className="flex items-start gap-3">
                            <Checkbox
                              checked={task.completed}
                              className="mt-0.5 data-[state=checked]:bg-teal-500 data-[state=checked]:border-teal-500"
                            />
                            <span
                              className={`text-sm ${
                                task.completed
                                  ? "text-gray-500 dark:text-gray-400 line-through"
                                  : "text-gray-700 dark:text-gray-300"
                              }`}
                            >
                              {task.text}
                            </span>
                          </div>
                        ))}

                        {/* Progress */}
                        <div className="pt-2">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-teal-600 dark:text-teal-400">Progress</span>
                            <span className="text-xs font-medium text-teal-600 dark:text-teal-400">
                              {phase.tasks.filter((t) => t.completed).length}/{phase.tasks.length}
                            </span>
                          </div>
                          <Progress
                            value={phase.progress}
                            className="h-1.5 bg-gray-200 dark:bg-gray-700 [&>div]:bg-gradient-to-r [&>div]:from-teal-500 [&>div]:to-emerald-500"
                          />
                        </div>
                      </div>
                    )}

                    {/* Skills */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Skills</h4>
                      <div className="flex flex-wrap gap-2">
                        {phase.skills.map((skill, index) => (
                          <span
                            key={skill}
                            className={`px-2 py-1 rounded-md text-xs font-medium border ${
                              index % 3 === 0
                                ? "bg-teal-50 dark:bg-teal-900/30 text-teal-700 border-teal-200 dark:border-teal-800"
                                : index % 3 === 1
                                  ? "bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 border-emerald-200 dark:border-emerald-800"
                                  : "bg-blue-50 dark:bg-blue-900/30 text-blue-700 border-blue-200 dark:border-blue-800"
                            }`}
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
})
