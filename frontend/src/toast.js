import { reactive } from 'vue'

export const toasts = reactive([])
let n = 0

export function notify(texto, tipo = 'ok') {
  const id = ++n
  toasts.push({ id, texto, tipo })
  setTimeout(() => {
    const i = toasts.findIndex(t => t.id === id)
    if (i >= 0) toasts.splice(i, 1)
  }, 3500)
}
