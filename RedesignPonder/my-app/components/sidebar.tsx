"use client"

import { memo } from "react"
import { Button } from "@/components/ui/button"
import { Home, MessageSquare, FolderOpen, BarChart3, Settings, Menu, X, Moon, Sun, Sparkles } from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Progress } from "@/components/ui/progress"
import { useTheme } from "next-themes"
import Link from "next/link"

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  currentPage?: string
}

export const Sidebar = memo(function Sidebar({ collapsed, onToggle, currentPage = "dashboard" }: SidebarProps) {
  const { theme, setTheme } = useTheme()

  const navigationItems = [
    {
      icon: Home,
      label: "Dashboard",
      href: "/",
      active: currentPage === "dashboard",
    },
    {
      icon: MessageSquare,
      label: "Chat",
      href: "/chat",
      active: currentPage === "chat",
    },
    {
      icon: FolderOpen,
      label: "Projects",
      href: "/projects",
      active: currentPage === "projects",
    },
    {
      icon: BarChart3,
      label: "Analytics",
      href: "/analytics",
      active: currentPage === "analytics",
    },
  ]

  // Dummy data for XP and Level
  const currentLevel = 7
  const currentXp = 345
  const xpToNextLevel = 500
  const xpProgress = (currentXp / xpToNextLevel) * 100

  return (
    <div className="h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200 dark:border-gray-700">
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-teal-500 to-blue-500 flex items-center justify-center">
              <span className="text-white font-bold text-sm">U</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900 dark:text-white">upSkillmee</h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">AI Learning Mentor</p>
            </div>
          </div>
        )}

        <Button
          onClick={onToggle}
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0 hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          {collapsed ? <Menu className="h-4 w-4" /> : <X className="h-4 w-4" />}
        </Button>
      </div>

      {/* Navigation */}
      <div className="flex-1 px-3 py-4">
        <nav className="space-y-1">
          {navigationItems.map((item) => (
            <Link key={item.label} href={item.href}>
              <Button
                variant="ghost"
                className={`w-full ${collapsed ? "justify-center px-0 h-10" : "justify-start px-3 h-10"} transition-colors ${
                  item.active
                    ? "bg-teal-50 dark:bg-teal-900/20 text-teal-700 dark:text-teal-300 hover:bg-teal-100 dark:hover:bg-teal-900/30"
                    : "text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700"
                }`}
              >
                <item.icon className="h-4 w-4 flex-shrink-0" />
                {!collapsed && <span className="ml-3 text-sm font-medium">{item.label}</span>}
              </Button>
            </Link>
          ))}
        </nav>
      </div>

      {/* User Profile, XP Bar, Theme Toggle & Settings */}
      <div className="mt-auto p-3 border-t border-gray-200 dark:border-gray-700">
        {/* Main row: Profile, Theme, Settings */}
        <div className={`flex items-center gap-2 ${collapsed ? "justify-center" : "justify-between"}`}>
          {/* User Profile Link */}
          <Link href="/profile" className={`group flex items-center gap-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200 ${collapsed ? "flex-1 justify-center" : "flex-1 min-w-0"}`}>
            <Avatar className="h-9 w-9 ring-2 ring-teal-500/20 dark:ring-teal-400/30 group-hover:scale-105 transition-transform duration-200">
              <AvatarImage src="/user-profile-illustration.png" />
              <AvatarFallback className="bg-gradient-to-br from-teal-500 to-emerald-500 text-white font-medium text-sm">
                JD
              </AvatarFallback>
            </Avatar>
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-900 dark:text-white text-sm truncate group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors duration-200">John Doe</p>
                {/* Removed "Learning Mode" dot and text */}
              </div>
            )}
          </Link>

          {/* Theme Toggle Button (always icon) */}
          <Button
            variant="ghost"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            size="icon"
            className="h-9 w-9 p-0 hover:bg-gray-100 dark:hover:bg-gray-700 flex-shrink-0 transition-colors duration-200"
          >
            {theme === "dark" ? (
              <Moon className="h-4 w-4 text-blue-500" />
            ) : (
              <Sun className="h-4 w-4 text-yellow-500" />
            )}
            <span className="sr-only">Toggle theme</span>
          </Button>

          {/* Settings Button (always icon) */}
          <Link href="/settings" className="flex-shrink-0">
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 p-0 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
            >
              <Settings className="h-4 w-4" />
              <span className="sr-only">Settings</span>
            </Button>
          </Link>
        </div>

        {/* XP Bar (only visible when not collapsed) */}
        {!collapsed && (
          <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 space-y-1 transition-all duration-200">
            <div className="flex items-center justify-between text-xs font-medium text-gray-700 dark:text-gray-300">
              <div className="flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-yellow-500" />
                <span>Level {currentLevel}</span>
              </div>
              <span>{currentXp}/{xpToNextLevel} XP</span>
            </div>
            <Progress
              value={xpProgress}
              className="h-1.5 bg-gray-200 dark:bg-gray-600 [&>div]:bg-gradient-to-r [&>div]:from-yellow-500 [&>div]:to-orange-500"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400">Next level in {xpToNextLevel - currentXp} XP</p>
          </div>
        )}
      </div>
    </div>
  )
})
