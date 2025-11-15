import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Moon, Sun, Bell, Info } from 'lucide-react'

const Settings = ({ onThemeChange }) => {
  const [darkMode, setDarkMode] = useState(false)

  const handleThemeToggle = () => {
    const newDarkMode = !darkMode
    setDarkMode(newDarkMode)
    if (onThemeChange) {
      onThemeChange(newDarkMode ? 'dark' : 'light')
    }
  }

  const settingsItems = [
    {
      icon: darkMode ? Moon : Sun,
      title: 'Mode sombre',
      description: 'Activer le thème sombre',
      action: handleThemeToggle,
      type: 'toggle',
      value: darkMode
    },
    {
      icon: Bell,
      title: 'Notifications',
      description: 'Gérer les notifications',
      action: () => {},
      type: 'button'
    },
    {
      icon: Info,
      title: 'À propos',
      description: 'Version 1.0.0',
      action: () => {},
      type: 'button'
    }
  ]

  return (
    <div className="px-4 py-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Paramètres</h2>
        
        <div className="space-y-2">
          {settingsItems.map((item, index) => {
            const Icon = item.icon
            
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                whileTap={{ scale: 0.98 }}
              >
                <button
                  onClick={item.action}
                  className="w-full bg-gray-50 rounded-2xl p-4 flex items-center justify-between hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-full bg-apple-blue/10 flex items-center justify-center">
                      <Icon className="w-5 h-5 text-apple-blue" />
                    </div>
                    <div className="text-left">
                      <p className="font-medium text-gray-900 text-sm">{item.title}</p>
                      <p className="text-gray-500 text-xs mt-0.5">{item.description}</p>
                    </div>
                  </div>
                  
                  {item.type === 'toggle' && (
                    <motion.div
                      className={`w-12 h-6 rounded-full p-1 ${
                        item.value ? 'bg-apple-blue' : 'bg-gray-300'
                      }`}
                      animate={{
                        backgroundColor: item.value ? '#007AFF' : '#D1D1D6'
                      }}
                    >
                      <motion.div
                        className="w-4 h-4 bg-white rounded-full shadow-md"
                        animate={{
                          x: item.value ? 24 : 0
                        }}
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                      />
                    </motion.div>
                  )}
                </button>
              </motion.div>
            )
          })}
        </div>
      </motion.div>
    </div>
  )
}

export default Settings


