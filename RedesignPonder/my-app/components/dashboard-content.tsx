"use client"

import { memo } from "react"
import { DashboardHeader } from "@/components/dashboard-header"
import { StatsGrid } from "@/components/stats-grid"
import { LearningProgress } from "@/components/learning-progress"
import { TasksList } from "@/components/tasks-list"
import { ActivityFeed } from "@/components/activity-feed"

interface DashboardContentProps {
}

export const DashboardContent = memo(function DashboardContent({}: DashboardContentProps) {
  return (
    <>
      {/* Header */}
      <DashboardHeader />

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto p-6 space-y-6">
          {/* Removed WelcomeSection */}
          <StatsGrid />

          {/* Main Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column */}
            <div className="lg:col-span-2 space-y-6">
              <LearningProgress />
              <TasksList />
            </div>

            {/* Right Column */}
            <div className="lg:col-span-1">
              <ActivityFeed />
            </div>
          </div>
        </div>
      </div>
    </>
  )
})
