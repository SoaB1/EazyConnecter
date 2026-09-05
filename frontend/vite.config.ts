import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  base: "./", // pywebviewでローカルのindex.htmlを読むため、絶対パスではなく相対パスでアセットを解決する
  plugins: [react()],
})
