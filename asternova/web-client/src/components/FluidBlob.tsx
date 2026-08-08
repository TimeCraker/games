"use client"

import { motion } from "framer-motion"

import styles from "./FluidBlob.module.css"

const easeOutExpo = [0.22, 1, 0.36, 1] as const

export function FluidBlob() {
  return (
    <motion.div
      className={styles.blobWrap}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.9, ease: easeOutExpo }}
      aria-hidden="true"
    >
      <div className={styles.blob} />
      <div className={styles.blobInnerGlow} />
    </motion.div>
  )
}
