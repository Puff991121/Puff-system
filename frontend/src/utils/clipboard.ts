export const copyText = async (text: string): Promise<void> => {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return
    }
  } catch {
    // Fall back to selection-based copying when clipboard permissions are unavailable.
  }

  const previousFocus = document.activeElement as HTMLElement | null
  const input = document.createElement('textarea')
  input.value = text
  input.readOnly = true
  input.style.cssText = 'position:fixed;left:-9999px;top:0;'
  input.setAttribute('aria-label', '复制链接')
  document.body.appendChild(input)
  let copied = false
  try {
    input.select()
    copied = document.execCommand('copy')
  } finally {
    input.remove()
    previousFocus?.focus({ preventScroll: true })
  }
  if (!copied) throw new Error('Copy failed')
}
