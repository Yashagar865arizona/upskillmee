import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Check, X, GraduationCap, Loader2 } from 'lucide-react'

interface Message {
  id: string
  type: "user" | "ai"
  content: string
  timestamp: Date
  isLearningPlan?: boolean
  isLoading?: boolean
}

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  if (message.isLoading) {
    return (
      <div className="flex gap-3"> {/* Reduced gap */}
        <Avatar className="h-8 w-8 mt-1">
          <AvatarFallback className="bg-gradient-to-br from-teal-500 to-emerald-500 text-white text-xs">
            <GraduationCap className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-lg rounded-tl-md px-4 py-3 border border-gray-200 dark:border-gray-600"> {/* Reduced rounded, changed bg/border */}
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-teal-500" />
            <div className="flex gap-1">
              <div className="w-1.5 h-1.5 bg-teal-500 rounded-full animate-bounce"></div> {/* Reduced size, changed color */}
              <div
                className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce"
                style={{ animationDelay: "0.1s" }}
              ></div>
              <div
                className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce"
                style={{ animationDelay: "0.2s" }}
              ></div>
            </div>
            <span className="text-sm text-gray-500 dark:text-gray-400">AI is thinking...</span>
          </div>
        </div>
      </div>
    )
  }

  if (message.type === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[70%] bg-gradient-to-br from-teal-500 to-emerald-500 text-white rounded-lg rounded-br-md px-4 py-3 shadow-sm"> {/* Reduced rounded, changed shadow */}
          <p className="text-sm leading-relaxed">{message.content}</p>
        </div>
      </div>
    )
  }

  if (message.isLearningPlan) {
    return (
      <div className="flex gap-3"> {/* Reduced gap */}
        <Avatar className="h-8 w-8 mt-1">
          <AvatarFallback className="bg-gradient-to-br from-teal-500 to-emerald-500 text-white text-xs">
            <GraduationCap className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 space-y-4">
          <div className="bg-gray-100 dark:bg-gray-700 rounded-lg rounded-tl-md px-4 py-3 border border-gray-200 dark:border-gray-600"> {/* Reduced rounded, changed bg/border */}
            <p className="text-gray-900 dark:text-white text-sm leading-relaxed mb-4">{message.content}</p>

            {/* Learning Plan Card */}
            <Card className="bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 p-5 rounded-lg shadow-sm relative overflow-hidden"> {/* Reduced padding, rounded */}
              {/* Gradient accent */}
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-teal-500 via-emerald-500 to-cyan-500"></div>

              <div className="space-y-4"> {/* Reduced spacing */}
                <div className="relative">
                  <div className="absolute -top-1 -left-1 w-3 h-3 bg-gradient-to-r from-teal-500 to-emerald-500 rounded-full animate-pulse shadow-sm"></div> {/* Reduced size, changed shadow */}
                  <h3 className="text-base font-semibold bg-gradient-to-r from-teal-600 to-emerald-600 dark:from-teal-400 dark:to-emerald-400 bg-clip-text text-transparent mb-1"> {/* Reduced font size */}
                    Learning Plan: Build a Recommendation Engine
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                    A 4-week project-based journey from Python basics to deploying a working recommendation system for
                    e-commerce, covering collaborative filtering, content-based filtering, and hybrid approaches.
                  </p>
                </div>

                <div className="flex flex-wrap gap-1.5"> {/* Reduced gap */}
                  <Badge className="bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/20 dark:text-teal-300 dark:border-teal-800 text-xs px-2 py-0.5"> {/* Reduced padding/font size */}
                    #Python
                  </Badge>
                  <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/20 dark:text-emerald-300 dark:border-emerald-800 text-xs px-2 py-0.5">
                    #MachineLearning
                  </Badge>
                  <Badge className="bg-cyan-50 text-cyan-700 border-cyan-200 dark:bg-cyan-950/20 dark:text-cyan-300 dark:border-cyan-800 text-xs px-2 py-0.5">
                    #Flask
                  </Badge>
                  <Badge className="bg-teal-50 text-teal-700 border-teal-200 dark:bg-teal-950/20 dark:text-teal-300 dark:border-teal-800 text-xs px-2 py-0.5">
                    #DataAnalysis
                  </Badge>
                </div>

                <div className="flex gap-2 pt-2"> {/* Reduced gap */}
                  <Button className="bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 text-white rounded-md px-3 py-1.5 text-sm font-medium shadow-sm transition-all duration-300"> {/* Reduced padding/font size, rounded */}
                    <Check className="h-4 w-4 mr-2" />
                    Accept & Start Learning
                  </Button>
                  <Button
                    variant="outline"
                    className="border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md px-3 py-1.5 text-sm font-medium bg-transparent transition-all duration-300"
                  >
                    <X className="h-4 w-4 mr-2" />
                    Customize Plan
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-3"> {/* Reduced gap */}
      <Avatar className="h-8 w-8 mt-1">
        <AvatarFallback className="bg-gradient-to-br from-teal-500 to-emerald-500 text-white text-xs">
          <GraduationCap className="h-4 w-4" />
        </AvatarFallback>
      </Avatar>
      <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-lg rounded-tl-md px-4 py-3 border border-gray-200 dark:border-gray-600"> {/* Reduced rounded, changed bg/border */}
        <p className="text-gray-900 dark:text-white text-sm leading-relaxed">{message.content}</p>
      </div>
    </div>
  )
}
