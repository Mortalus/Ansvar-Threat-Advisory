/**
 * Pipeline ID Manager
 * 
 * A bulletproof system for managing pipeline IDs that can NEVER be lost.
 * This is a singleton that manages pipeline ID across all storage mechanisms.
 */

class PipelineIdManager {
  private static instance: PipelineIdManager
  private currentId: string | null = null
  private readonly STORAGE_KEYS = {
    localStorage: 'pipeline_id_backup',
    sessionStorage: 'pipeline_id_session',
  }

  private constructor() {
    // Try to recover on initialization
    this.recoverFromStorage()
  }

  static getInstance(): PipelineIdManager {
    if (!PipelineIdManager.instance) {
      PipelineIdManager.instance = new PipelineIdManager()
    }
    return PipelineIdManager.instance
  }

  /**
   * Set the pipeline ID and save to all storage locations
   */
  setPipelineId(id: string): void {
    console.log('🔒 PipelineIdManager: Setting pipeline ID:', id)
    this.currentId = id
    
    // Save to all storage locations
    try {
      localStorage.setItem(this.STORAGE_KEYS.localStorage, id)
      sessionStorage.setItem(this.STORAGE_KEYS.sessionStorage, id)
      
      // Also save with timestamp for debugging
      const backup = {
        id,
        timestamp: new Date().toISOString(),
        source: 'PipelineIdManager'
      }
      localStorage.setItem('pipeline_id_backup_with_meta', JSON.stringify(backup))
      
      console.log('✅ Pipeline ID saved to all storage locations')
    } catch (e) {
      console.error('Failed to save pipeline ID to storage:', e)
    }
  }

  /**
   * Get the current pipeline ID, attempting recovery if needed
   */
  getPipelineId(): string | null {
    // If we have it in memory, return it
    if (this.currentId) {
      return this.currentId
    }

    // Otherwise, try to recover
    return this.recoverFromStorage()
  }

  /**
   * Attempt to recover pipeline ID from any available storage
   */
  recoverFromStorage(): string | null {
    console.log('🔍 PipelineIdManager: Attempting to recover pipeline ID...')
    
    // Try sessionStorage first (most recent)
    try {
      const sessionId = sessionStorage.getItem(this.STORAGE_KEYS.sessionStorage)
      if (sessionId) {
        console.log('✅ Recovered from sessionStorage:', sessionId)
        this.currentId = sessionId
        return sessionId
      }
    } catch (e) {
      console.error('Failed to check sessionStorage:', e)
    }

    // Try localStorage
    try {
      const localId = localStorage.getItem(this.STORAGE_KEYS.localStorage)
      if (localId) {
        console.log('✅ Recovered from localStorage:', localId)
        this.currentId = localId
        // Also restore to sessionStorage
        try {
          sessionStorage.setItem(this.STORAGE_KEYS.sessionStorage, localId)
        } catch (e) {
          // Ignore
        }
        return localId
      }
    } catch (e) {
      console.error('Failed to check localStorage:', e)
    }

    // Try backup with metadata
    try {
      const backupStr = localStorage.getItem('pipeline_id_backup_with_meta')
      if (backupStr) {
        const backup = JSON.parse(backupStr)
        if (backup.id) {
          console.log('✅ Recovered from backup with metadata:', backup)
          this.currentId = backup.id
          // Restore to all locations
          this.setPipelineId(backup.id)
          return backup.id
        }
      }
    } catch (e) {
      console.error('Failed to check backup:', e)
    }

    // Check Zustand store as last resort
    try {
      const zustandStore = localStorage.getItem('threat-modeling-store')
      if (zustandStore) {
        const parsed = JSON.parse(zustandStore)
        const id = parsed?.state?.currentPipelineId || parsed?.state?.backupPipelineId
        if (id) {
          console.log('✅ Recovered from Zustand store:', id)
          this.currentId = id
          // Restore to all locations
          this.setPipelineId(id)
          return id
        }
      }
    } catch (e) {
      console.error('Failed to check Zustand store:', e)
    }

    console.log('❌ No pipeline ID could be recovered')
    return null
  }

  /**
   * Clear all stored pipeline IDs
   */
  clear(): void {
    this.currentId = null
    try {
      localStorage.removeItem(this.STORAGE_KEYS.localStorage)
      sessionStorage.removeItem(this.STORAGE_KEYS.sessionStorage)
      localStorage.removeItem('pipeline_id_backup_with_meta')
    } catch (e) {
      console.error('Failed to clear storage:', e)
    }
  }

  /**
   * Check if a pipeline ID is available
   */
  hasId(): boolean {
    return this.getPipelineId() !== null
  }
}

// Export singleton instance
export const pipelineIdManager = PipelineIdManager.getInstance()

// Helper hook for React components
export function usePipelineId() {
  const manager = PipelineIdManager.getInstance()
  
  return {
    setPipelineId: (id: string) => manager.setPipelineId(id),
    getPipelineId: () => manager.getPipelineId(),
    hasId: () => manager.hasId(),
    clear: () => manager.clear(),
  }
}