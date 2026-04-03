"use client"

import { useState, memo } from "react"
import { Sidebar } from "@/components/sidebar"
import { DashboardContent } from "@/components/dashboard-content"

export const DashboardPage = memo(function DashboardPage() {
  const [leftSidebarCollapsed, setLeftSidebarCollapsed] = useState(false)

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Left Sidebar */}
      <div className={`transition-all duration-300 ease-out ${leftSidebarCollapsed ? "w-16" : "w-64"}`}>
        <Sidebar
          collapsed={leftSidebarCollapsed}
          onToggle={() => setLeftSidebarCollapsed(!leftSidebarCollapsed)}
          currentPage="dashboard"
        />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Dashboard Content (including the top header) */}
        <DashboardContent />
      </div>
    </div>
  )
})
