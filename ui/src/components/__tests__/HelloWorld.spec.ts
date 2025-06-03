import { describe, it, expect } from 'vitest'

import { mount } from '@vue/test-utils'
import ComposeView from '@/views/ComposeView.vue'

describe('ComposeView', () => {
  it('renders properly', () => {
    const wrapper = mount(ComposeView, { props: { msg: 'Hello Vitest' } })
    expect(wrapper.text()).toContain('Hello Vitest')
  })
})
