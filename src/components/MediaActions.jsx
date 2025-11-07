import React from 'react'
import { motion } from 'framer-motion'

const MediaActions = ({ actions, isVisible, onActionClick }) => {
  return (
    <motion.div
      initial={{ y: 100, opacity: 0 }}
      animate={{ 
        y: isVisible ? 0 : 100,
        opacity: isVisible ? 1 : 0
      }}
      exit={{ y: 100, opacity: 0 }}
      transition={{ 
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1]
      }}
      className="absolute bottom-0 left-0 right-0 z-10 safe-area-bottom"
    >
      <div className="bg-gradient-to-t from-black/90 via-black/80 to-transparent pb-8 pt-4">
        <div className="max-w-md mx-auto px-4">
          <div className="grid grid-cols-4 gap-4">
            {actions.map((action, index) => {
              const Icon = action.icon
              
              return (
                <motion.button
                  key={action.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ 
                    opacity: isVisible ? 1 : 0,
                    y: isVisible ? 0 : 20
                  }}
                  transition={{ 
                    duration: 0.2,
                    delay: index * 0.05
                  }}
                  whileTap={{ scale: 0.95 }}
                  onClick={(e) => {
                    e.stopPropagation()
                    onActionClick(action)
                  }}
                  className="flex flex-col items-center justify-center space-y-2 py-3 px-2 rounded-2xl bg-white/10 backdrop-blur-md hover:bg-white/20 transition-colors active:bg-white/30"
                >
                  <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <span className="text-white text-xs font-medium text-center">
                    {action.label}
                  </span>
                </motion.button>
              )
            })}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default MediaActions

