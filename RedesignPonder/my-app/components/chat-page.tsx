"use client"

import { useState, memo } from "react"
import { Sidebar } from "@/components/sidebar"
import { ChatContainer } from "@/components/chat-container"
import { ProjectBoard } from "@/components/project-board"

export const ChatPage = memo(function ChatPage() {
  const [leftSidebarCollapsed, setLeftSidebarCollapsed] = useState(false)

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Left Sidebar */}
      <div className={`transition-all duration-300 ease-out ${leftSidebarCollapsed ? "w-16" : "w-64"}`}>
        <Sidebar
          collapsed={leftSidebarCollapsed}
          onToggle={() => setLeftSidebarCollapsed(!leftSidebarCollapsed)}
          currentPage="chat"
        />
      </div>

      {/* Chat Content */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex p-6 gap-6">
          {/* Chat Interface */}
          <div className="flex-1">
            <ChatContainer />
          </div>

          {/* Project Board */}
          <div className="w-80 flex-shrink-0">
            <ProjectBoard />
          </div>
        </div>
      </div>
    </div>
  )
})
