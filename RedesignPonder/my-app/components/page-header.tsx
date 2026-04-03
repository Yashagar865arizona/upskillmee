"use client"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Bell, ChevronDown } from "lucide-react"

export function PageHeader() {
  return (
    <div className="flex items-center justify-between p-4 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
      {/* Page Title */}
      <div>
        <h1 className="text-xl font-bold bg-gradient-to-r from-teal-600 to-emerald-600 dark:from-teal-400 dark:to-emerald-400 bg-clip-text text-transparent">
          Dashboard
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {new Date().toLocaleDateString("en-US", {
            weekday: "long",
            month: "short",
            day: "numeric",
          })}
        </p>
      </div>

      {/* User Profile Section */}
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <Button
          variant="ghost"
          size="sm"
          className="relative h-9 w-9 p-0 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <Bell className="h-4 w-4 text-gray-600 dark:text-gray-400" />
          <Badge className="absolute -top-1 -right-1 h-4 w-4 p-0 bg-gradient-to-r from-red-500 to-pink-500 text-white text-xs flex items-center justify-center">
            3
          </Badge>
        </Button>

        {/* User Profile */}
        <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer">
          <div className="text-right">
            <p className="font-semibold text-gray-900 dark:text-white text-sm">John Doe</p>
            <div className="flex items-center justify-end gap-1 mt-0.5">
              <span className="text-xs text-gray-500 dark:text-gray-400">Learning Mode</span>
              <div className="w-1.5 h-1.5 bg-gradient-to-r from-emerald-400 to-teal-400 rounded-full animate-pulse"></div>
            </div>
          </div>

          <Avatar className="h-8 w-8 ring-2 ring-teal-500/20 dark:ring-teal-400/30">
            <AvatarImage src="/placeholder.svg?height=32&width=32" />
            <AvatarFallback className="bg-gradient-to-br from-teal-500 to-emerald-500 text-white font-medium text-sm">
              JD
            </AvatarFallback>
          </Avatar>

          <ChevronDown className="h-3 w-3 text-gray-400" />
        </div>
      </div>
    </div>
  )
}
