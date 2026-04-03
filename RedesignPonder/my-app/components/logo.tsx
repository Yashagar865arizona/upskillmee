"use client"

interface LogoProps {
  size?: "sm" | "md" | "lg"
  collapsed?: boolean
}

export function Logo({ size = "md", collapsed = false }: LogoProps) {
  const sizeClasses = {
    sm: "w-8 h-8 text-base",
    md: "w-10 h-10 text-lg",
    lg: "w-12 h-12 text-xl",
  }

  if (collapsed) {
    return (
      <div
        className={`flex items-center justify-center rounded-lg bg-gradient-to-br from-teal-500 to-emerald-500 shadow-sm ${sizeClasses[size]}`}
      >
        <span className="text-white font-bold">U</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-3">
      <div
        className={`flex items-center justify-center rounded-lg bg-gradient-to-br from-teal-500 to-emerald-500 shadow-sm ${sizeClasses[size]}`}
      >
        {/* Replace this with your actual upSkillmee logo image */}
        <span className="text-white font-bold">U</span>
      </div>
      <div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          upSkillmee
        </h1>
        <p className="text-xs text-gray-500 dark:text-gray-400">AI Learning Mentor</p>
      </div>
    </div>
  )
}
