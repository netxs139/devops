import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ProductSelector from '@/components/ProductSelector.vue'
import { http } from '@/utils/request'

// Mock http module
vi.mock('@/utils/request', () => ({
  http: {
    get: vi.fn()
  }
}))

describe('ProductSelector.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Provide default mock implementation
    vi.mocked(http.get).mockImplementation((url) => {
      if (url === '/admin/products') {
        return Promise.resolve([{ product_id: 'p1', product_name: 'Product 1' }])
      }
      if (url === '/admin/organizations') {
        return Promise.resolve([{ org_id: 'o1', org_name: 'Org 1', org_level: 1 }])
      }
      return Promise.resolve([])
    })
  })

  it('renders correctly and switches segment', async () => {
    const wrapper = mount(ProductSelector, {
      props: {
        type: 'product',
        id: null
      }
    })

    // Wait for onMounted fetch
    await new Promise(resolve => setTimeout(resolve, 0))

    // Check if both segments are rendered
    const segments = wrapper.findAll('.segment')
    expect(segments.length).toBe(2)
    expect(segments[0].text()).toBe('产品')
    expect(segments[1].text()).toBe('部门')

    // Initial state check
    expect(segments[0].classes()).toContain('active')
    
    // Click on org segment
    await segments[1].trigger('click')

    // Verify emitted events
    const emittedType = wrapper.emitted('update:type')
    expect(emittedType).toBeTruthy()
    if (emittedType) {
        expect(emittedType[0]).toEqual(['org'])
    }
  })
})
