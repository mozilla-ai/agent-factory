import { describe, it, expect } from 'vitest'

import { mount } from '@vue/test-utils'
import ChatView from '@/views/ChatView.vue'

describe('ChatView', () => {
  it('renders properly', () => {
    const wrapper = mount(ChatView, { props: { msg: 'Hello Vitest' } })
    expect(wrapper.text()).toContain('Hello Vitest')
  })
})
