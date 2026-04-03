"use client"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Flame, Target } from "lucide-react"

export function DashboardHeader() {
  const currentHour = new Date().getHours()
  const greeting = currentHour < 12 ? "Good morning" : currentHour < 18 ? "Good afternoon" : "Good evening"

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="flex items-center gap-6">
        <Avatar className="h-16 w-16 ring-4 ring-teal-100 dark:ring-teal-900">
          <AvatarImage src="/placeholder.svg?height=64&width=64" />
          <AvatarFallback className="bg-gradient-to-br from-teal-500 to-emerald-500 text-white text-xl font-semibold">
            JD
          </AvatarFallback>
        </Avatar>
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-teal-600 to-emerald-600 dark:from-teal-400 dark:to-emerald-400 bg-clip-text text-transparent">
            {greeting}, John!
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 mt-1">Ready to continue your upSkillmee journey?</p>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Learning Streak */}
        <Card className="p-6 bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-950 dark:to-red-950 border-orange-200 dark:border-orange-800">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl">
              <Flame className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">15 Days</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Learning Streak</p>
            </div>
          </div>
        </Card>

        {/* Current Progress */}
        <Card className="p-6 bg-gradient-to-br from-teal-50 to-emerald-50 dark:from-teal-950 dark:to-emerald-950 border-teal-200 dark:border-teal-800">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-teal-500 to-emerald-500 rounded-xl">
              <Target className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">Week 2</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Python ML Journey</p>
            </div>
          </div>
        </Card>

        {/* Next Milestone */}
        <Card className="p-6 bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-950 dark:to-blue-950 border-purple-200 dark:border-purple-800">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">Next Milestone</p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Deploy ML Model</p>
            </div>
            <Badge className="bg-gradient-to-r from-purple-500 to-blue-500 text-white">3 days</Badge>
          </div>
        </Card>
      </div>
    </div>
  )
}
