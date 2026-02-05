import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ToastContainer } from './Toast'
import { useToastStore } from '@/stores/toastStore'

// Mock the store if needed, or 
// just use the real one and reset it
describe('ToastContainer', () => {
    beforeEach(() => {
        useToastStore.setState({ toasts: [] })
    })

    it('should render nothing when there are no toasts', () => {
        const { container } = render(<ToastContainer />)
        expect(container).toBeEmptyDOMElement()
    })

    it('should render a toast message', () => {
        useToastStore.setState({
            toasts: [
                { id: '1', message: 'Success message', type: 'success' }
            ]
        })

        render(<ToastContainer />)
        expect(screen.getByText('Success message')).toBeDefined()
    })

    it('should call removeToast when close button is clicked', () => {
        const removeToastSpy = vi.fn()
        useToastStore.setState({
            toasts: [
                { id: '1', message: 'Close me', type: 'info' }
            ],
            removeToast: removeToastSpy
        })

        render(<ToastContainer />)
        const closeButton = screen.getByRole('button')
        fireEvent.click(closeButton)

        expect(removeToastSpy).toHaveBeenCalledWith('1')
    })

    it('should render multiple toasts', () => {
        useToastStore.setState({
            toasts: [
                { id: '1', message: 'Toast 1', type: 'success' },
                { id: '2', message: 'Toast 2', type: 'error' }
            ]
        })

        render(<ToastContainer />)
        expect(screen.getByText('Toast 1')).toBeDefined()
        expect(screen.getByText('Toast 2')).toBeDefined()
    })
})
