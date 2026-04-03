"use client"

import { memo } from "react"
import { Button } from "@/components/ui/button"
import { Zap, Target } from 'lucide-react'

export const WelcomeSection = memo(function WelcomeSection() {
  return (
    <div className="text-center space-y-4">
      <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-teal-50 dark:bg-teal-900/20 rounded-full border border-teal-200 dark:border-teal-800">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
        <span className="text-xs font-medium text-teal-700 dark:text-teal-300">Welcome back, John! 👋</span>
      </div>

      <div className="space-y-3">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Ready to continue learning?
        </h1>
        <p className="text-base text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
          Pick up where you left off and keep building your skills with AI-powered guidance.
        </p>
      </div>

      <div className="flex items-center justify-center gap-3">
        <Button className="bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white px-5 py-2 text-sm">
          <Zap className="h-4 w-4 mr-2" />
          Continue Learning
        </Button>
        <Button variant="outline" className="px-5 py-2 text-sm">
          <Target className="h-4 w-4 mr-2" />
          Set New Goal
        </Button>
      </div>
    </div>
  )
})
