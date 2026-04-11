<template>
  <div class="consult-page">
    <section class="consult-hero">
      <div>
        <div class="hero-kicker">智能问答</div>
        <h2>病害咨询助手</h2>
        <p class="hero-desc">描述当前作物症状、种植环境和处理情况，系统将给出分步建议与观察要点。</p>
      </div>
    </section>

    <section class="consult-layout">
      <article class="panel quick-panel">
        <h3>快捷问题</h3>
        <div class="quick-list">
          <button
            v-for="item in quickQuestions"
            :key="item"
            class="quick-btn"
            @click="useQuickQuestion(item)"
          >
            {{ item }}
          </button>
        </div>
        <p class="tip-text">你也可以补充：作物品种、发病部位、天气湿度、近 3 天用药情况。</p>
      </article>

      <article class="panel chat-panel">
        <div ref="chatBodyRef" class="chat-body">
          <div
            v-for="item in messages"
            :key="item.id"
            class="chat-item"
            :class="[item.role, { pending: item.pending }]"
          >
            <div class="chat-role">{{ item.role === 'user' ? '我' : '咨询助手' }}</div>
            <p class="chat-text">{{ item.content }}</p>
          </div>
        </div>

        <div class="input-area">
          <textarea
            v-model="question"
            class="question-input"
            rows="4"
            placeholder="请输入病害问题，例如：番茄叶片出现褐色斑点并伴随卷叶，连续阴雨后加重，应该先做什么？"
            @keydown.enter.exact.prevent="handleSubmit"
          ></textarea>
          <div class="actions-row">
            <span class="hint">按 Enter 发送，Shift + Enter 换行</span>
            <button class="primary-btn" :disabled="submitting" @click="handleSubmit">
              {{ submitting ? '咨询中...' : '发送咨询' }}
            </button>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { submitDiseaseConsult, type ConsultMessage } from '../api/consult'

type ChatItem = {
  id: number
  role: 'user' | 'assistant'
  content: string
  pending?: boolean
}

const question = ref('')
const submitting = ref(false)
const chatBodyRef = ref<HTMLElement | null>(null)
const quickQuestions = [
  '叶片出现黄色斑点，可能是什么病害？',
  '连续阴雨后病情加重，田间应急怎么处理？',
  '已经打药两次效果不明显，下一步建议是什么？',
  '如何区分病害与缺素导致的叶片异常？',
]

const messages = ref<ChatItem[]>([
  {
    id: 1,
    role: 'assistant',
    content: '你好，我是病害咨询助手。请告诉我作物类型、症状表现和近期环境信息，我会给你可执行的处理建议。',
  },
])

function useQuickQuestion(text: string) {
  question.value = text
}

function extractAnswer(payload: any): string {
  if (typeof payload === 'string' && payload.trim()) return payload.trim()
  if (payload && typeof payload === 'object') {
    const candidates = [payload.answer, payload.reply, payload.content, payload.result]
    const match = candidates.find((item) => typeof item === 'string' && item.trim())
    if (typeof match === 'string') return match.trim()
  }
  return '已收到你的咨询问题。请继续补充作物类型、发病时间和田间环境，便于给出更精确建议。'
}

function conversationHistory(): ConsultMessage[] {
  return messages.value
    .slice(-8)
    .map((item) => ({ role: item.role, content: item.content }))
}

async function scrollToBottom() {
  await nextTick()
  if (chatBodyRef.value) {
    chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
  }
}

async function handleSubmit() {
  const text = question.value.trim()
  if (!text || submitting.value) return

  const userMessage: ChatItem = {
    id: Date.now(),
    role: 'user',
    content: text,
  }
  messages.value.push(userMessage)
  question.value = ''
  await scrollToBottom()

  submitting.value = true
  const pendingMessageId = Date.now() + 1
  messages.value.push({
    id: pendingMessageId,
    role: 'assistant',
    content: '正在思考中...',
    pending: true,
  })
  await scrollToBottom()
  try {
    const res: any = await submitDiseaseConsult({
      question: text,
      history: conversationHistory(),
    })
    const answer = extractAnswer(res?.data ?? res)
    const pendingIndex = messages.value.findIndex((item) => item.id === pendingMessageId)
    if (pendingIndex >= 0) {
      messages.value[pendingIndex] = {
        id: pendingMessageId,
        role: 'assistant',
        content: answer,
      }
    } else {
      messages.value.push({ id: pendingMessageId, role: 'assistant', content: answer })
    }
  } catch (error: any) {
    const errMessage = String(error?.message || '')
    const fallbackContent = errMessage.includes('暂未配置')
      ? '咨询接口尚未接入，页面已准备完成。你把 API 发我后，我会立刻接上并联调。'
      : '咨询服务暂时不可用，请稍后重试。'
    const pendingIndex = messages.value.findIndex((item) => item.id === pendingMessageId)
    if (pendingIndex >= 0) {
      messages.value[pendingIndex] = {
        id: pendingMessageId,
        role: 'assistant',
        content: fallbackContent,
      }
    } else {
      messages.value.push({
        id: pendingMessageId,
        role: 'assistant',
        content: fallbackContent,
      })
    }
    if (!errMessage.includes('暂未配置')) {
      ElMessage.error('咨询失败，请稍后重试')
    }
  } finally {
    submitting.value = false
    await scrollToBottom()
  }
}
</script>

<style scoped>
.consult-page {
  padding: 28px;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  box-sizing: border-box;
  overflow: hidden;
}

.consult-hero {
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, rgba(248, 233, 237, 0.9), rgba(234, 243, 241, 0.9));
  border: 1px solid rgba(220, 210, 218, 0.68);
  padding: 24px 26px;
  box-shadow: var(--shadow-soft);
}

.hero-kicker {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--pink-light);
  color: var(--pink-deep);
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 8px;
}

.consult-hero h2 {
  margin: 0;
  font-size: 30px;
  color: var(--text-primary);
}

.hero-desc {
  margin: 8px 0 0;
  color: var(--text-secondary);
  line-height: 1.65;
}

.consult-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 20px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.panel {
  border-radius: var(--radius-md);
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--shadow-soft);
}

.quick-panel {
  padding: 18px;
  overflow-y: auto;
}

.quick-panel h3 {
  margin: 2px 0 12px;
  font-size: 20px;
}

.quick-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quick-btn {
  border: 1px solid #eed7df;
  background: #fff;
  color: var(--text-primary);
  border-radius: 12px;
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
}

.quick-btn:hover {
  border-color: var(--pink);
  background: var(--pink-light);
}

.tip-text {
  margin-top: 14px;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.6;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.chat-body {
  flex: 1;
  min-height: 0;
  padding: 16px;
  overflow-y: auto;
  border-bottom: 1px solid #f1e4eb;
}

.chat-item {
  margin-bottom: 12px;
  max-width: 84%;
}

.chat-role {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.chat-text {
  margin: 0;
  padding: 10px 12px;
  border-radius: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
  color: var(--text-primary);
  font-size: 14px;
}

.chat-item.user {
  margin-left: auto;
}

.chat-item.user .chat-role {
  text-align: right;
}

.chat-item.user .chat-text {
  background: linear-gradient(135deg, rgba(242, 199, 178, 0.55), rgba(215, 161, 173, 0.5));
}

.chat-item.assistant .chat-text {
  background: linear-gradient(135deg, rgba(234, 243, 241, 0.9), rgba(242, 236, 241, 0.85));
}

.chat-item.pending .chat-text {
  opacity: 0.9;
  font-style: italic;
}

.input-area {
  padding: 14px;
}

.question-input {
  width: 100%;
  resize: none;
  border-radius: 12px;
  border: 1px solid #e7d8e0;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  box-sizing: border-box;
  font-family: inherit;
}

.question-input:focus {
  outline: none;
  border-color: var(--pink);
  box-shadow: 0 0 0 3px rgba(215, 161, 173, 0.15);
}

.actions-row {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.hint {
  color: var(--text-muted);
  font-size: 12px;
}

.primary-btn {
  border: 0;
  border-radius: 12px;
  background: var(--pink-deep);
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  padding: 10px 18px;
  cursor: pointer;
}

.primary-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

@media (max-width: 992px) {
  .consult-page {
    height: auto;
    min-height: 100%;
    overflow: visible;
  }

  .consult-layout {
    grid-template-columns: 1fr;
    overflow: visible;
  }

  .quick-panel {
    order: 2;
  }

  .chat-panel {
    order: 1;
    min-height: 520px;
    height: auto;
  }
}
</style>
