import { describe, it, expect, beforeEach } from 'vitest'
import { useToastStore } from './toastStore'

describe('toastStore', () => {
    beforeEach(() => {
        // Clear the store before each test
        useToastStore.setState({ toasts: [] })
    })

    it('should add a toast', () => {
        const { addToast } = useToastStore.getState()
        addToast('Test message', 'success')

        const { toasts } = useToastStore.getState()
        expect(toasts).toHaveLength(1)
        expect(toasts[0]).toMatchObject({
            message: 'Test message',
            type: 'success',
        })
        expect(toasts[0].id).toBeDefined()
    })

    it('should remove a toast by id', () => {
        const { addToast, removeToast } = useToastStore.getState()

        addToast('Toast 1', 'info')
        const { toasts: beforeToasts } = useToastStore.getState()
        const toastId = beforeToasts[0].id

        removeToast(toastId)
        const { toasts: afterToasts } = useToastStore.getState()
        expect(afterToasts).toHaveLength(0)
    })

    it('should handle multiple toasts', () => {
        const { addToast } = useToastStore.getState()

        addToast('Message 1', 'success')
        addToast('Message 2', 'error')

        const { toasts } = useToastStore.getState()
        expect(toasts).toHaveLength(2)
        expect(toasts[0].message).toBe('Message 1')
        expect(toasts[1].message).toBe('Message 2')
    })
})
