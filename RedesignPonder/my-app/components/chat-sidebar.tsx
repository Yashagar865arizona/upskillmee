"use client"

import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Home, MessageSquare, FolderOpen, BarChart3, Settings, Menu, X, Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import Link from "next/link"
import { usePathname } from "next/navigation"

interface ChatSidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export function ChatSidebar({ collapsed, onToggle }: ChatSidebarProps) {
  const { theme, setTheme } = useTheme()
  const pathname = usePathname()

  const navigationItems = [
    { icon: Home, label: "Dashboard", href: "/dashboard", active: pathname === "/dashboard" },
    { icon: MessageSquare, label: "Chat", href: "/chat", active: pathname === "/chat" },
    { icon: FolderOpen, label: "My Projects", href: "/projects", active: pathname === "/projects" },
    { icon: BarChart3, label: "Analytics", href: "/analytics", active: pathname === "/analytics" },
    { icon: Settings, label: "Settings", href: "/settings", active: pathname === "/settings" },
  ]

  return (
    <div className="h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 flex flex-col relative shadow-sm">
      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-teal-500/3 via-emerald-500/2 to-cyan-500/3 dark:from-teal-400/5 dark:via-emerald-400/3 dark:to-cyan-400/5 pointer-events-none"></div>

      {/* Header with Brand and Toggle */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-800 relative z-10">
        <div className="flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-teal-500 to-emerald-500 shadow-lg shadow-teal-500/25">
              <span className="text-white font-bold text-sm">U</span>
            </div>

            {!collapsed && (
              <div>
                <h1 className="text-lg font-bold bg-gradient-to-r from-teal-600 to-emerald-600 dark:from-teal-400 dark:to-emerald-400 bg-clip-text text-transparent">
                  upSkillmee
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">AI Learning Mentor</p>
              </div>
            )}
          </div>

          {/* Toggle Button */}
          <Button
            onClick={onToggle}
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 hover:bg-gradient-to-r hover:from-teal-500/20 hover:to-emerald-500/20 dark:hover:from-teal-400/30 dark:hover:to-emerald-400/30 transition-all duration-300 rounded-lg"
          >
            {collapsed ? <Menu className="h-4 w-4" /> : <X className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 px-4 py-4 relative z-10">
        <nav className="space-y-2">
          {navigationItems.map((item) => (
            <Link key={item.label} href={item.href}>
              <Button
                variant="ghost"
                className={`w-full ${collapsed ? "justify-center px-0 h-10" : "justify-start px-3 h-10"} gap-3 transition-all duration-300 rounded-lg ${
                  item.active
                    ? "bg-gradient-to-r from-teal-50 to-emerald-50 dark:from-teal-950/50 dark:to-emerald-950/50 text-teal-700 dark:text-teal-300 border border-teal-200/50 dark:border-teal-800/50 shadow-lg shadow-teal-500/10 dark:shadow-teal-400/20"
                    : "text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gradient-to-r hover:from-teal-50/50 hover:to-emerald-50/50 dark:hover:from-teal-900/20 dark:hover:to-emerald-900/20"
                }`}
              >
                <item.icon
                  className={`h-4 w-4 flex-shrink-0 ${item.active ? "text-teal-600 dark:text-teal-400" : ""}`}
                />
                {!collapsed && <span className="font-medium text-sm">{item.label}</span>}
              </Button>
            </Link>
          ))}
        </nav>
      </div>

      {/* Dark Mode Toggle at Bottom */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-800 relative z-10">
        {!collapsed ? (
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Theme</span>
            <div className="flex items-center gap-2">
              <Sun className="h-4 w-4 text-amber-500" />
              <Switch
                checked={theme === "dark"}
                onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
                className="data-[state=checked]:bg-gradient-to-r data-[state=checked]:from-teal-500 data-[state=checked]:to-emerald-500"
              />
              <Moon className="h-4 w-4 text-blue-500" />
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <Button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 hover:bg-gradient-to-r hover:from-teal-500/20 hover:to-emerald-500/20 dark:hover:from-teal-400/30 dark:hover:to-emerald-400/30 transition-all duration-300 rounded-lg"
            >
              {theme === "dark" ? (
                <Sun className="h-4 w-4 text-amber-500" />
              ) : (
                <Moon className="h-4 w-4 text-blue-500" />
              )}
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
