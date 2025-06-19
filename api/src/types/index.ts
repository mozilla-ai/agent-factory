export interface FileEntry {
  name: string
  isDirectory: boolean
  files?: FileEntry[]
}

export type OutputCallback = (source: 'stdout' | 'stderr', text: string) => void
