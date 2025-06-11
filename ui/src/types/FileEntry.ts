export interface FileEntry {
  name: string
  isDirectory: boolean
  files?: FileEntry[]
}

export interface TransformedFileEntry extends FileEntry {
  path: string
}
