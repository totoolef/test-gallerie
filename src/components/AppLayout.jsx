import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Header from './Header'
import BottomNav from './BottomNav'

const AppLayout = ({ children, activeTab, onTabChange, headerTitle }) => {
  return (
    <div className="min-h-screen bg-white w-full md:max-w-[430px] md:mx-auto relative overflow-hidden">
      <Header title={headerTitle} />
      
      <main className="pt-20 pb-20 min-h-screen">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>
      
      <BottomNav activeTab={activeTab} onTabChange={onTabChange} />
    </div>
  )
}

export default AppLayout

