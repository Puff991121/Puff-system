<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { Calendar, Check, Clock, Delete, Edit, Plus, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  createTodo, deleteTodo, getTodos, getTodoSummary, updateTodo,
  type Todo, type TodoPayload, type TodoPeriod, type TodoPriority, type TodoStatus,
} from '@/api/todos'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const rows = ref<Todo[]>([])
const loading = ref(false)
const submitting = ref(false)
const togglingId = ref<number | null>(null)
const page = ref(1)
const total = ref(0)
const activePeriod = ref<TodoPeriod>('daily')
const status = ref<TodoStatus | ''>('')
const keyword = ref('')
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const summary = reactive({ total: 0, pending: 0, completed: 0, overdue: 0, daily: 0, weekly: 0, monthly: 0, completion_rate: 0 })
const form = reactive<TodoPayload>({ title: '', description: '', period_type: 'daily', scheduled_date: '', priority: 'medium' })
const rules: FormRules = {
  title: [{ required: true, message: '请输入待办标题', trigger: 'blur' }],
  scheduled_date: [{ required: true, message: '请选择计划日期', trigger: 'change' }],
  period_type: [{ required: true, message: '请选择待办周期', trigger: 'change' }],
}

const periods: Array<{ value: TodoPeriod; label: string; english: string }> = [
  { value: 'daily', label: '每日待办', english: 'DAY' },
  { value: 'weekly', label: '每周待办', english: 'WEEK' },
  { value: 'monthly', label: '每月待办', english: 'MONTH' },
]
const today = () => {
  const d = new Date(), pad = (value: number) => String(value).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}
const periodCount = (period: TodoPeriod) => summary[period]
const currentLabel = computed(() => periods.find(item => item.value === activePeriod.value)?.label || '')
const completionStyle = computed(() => ({ '--progress': `${summary.completion_rate * 3.6}deg` }))
const priorityText: Record<TodoPriority, string> = { high: '高优先级', medium: '中优先级', low: '低优先级' }
const periodText: Record<TodoPeriod, string> = { daily: '每日', weekly: '每周', monthly: '每月' }
const friendlyDate = (value: string) => {
  const date = new Date(`${value}T00:00:00`), current = new Date(`${today()}T00:00:00`)
  const offset = Math.round((date.getTime() - current.getTime()) / 86400000)
  if (offset === 0) return '今天'
  if (offset === 1) return '明天'
  if (offset === -1) return '昨天'
  return `${date.getMonth() + 1}月${date.getDate()}日`
}
const isOverdue = (row: Todo) => row.status === 'pending' && row.scheduled_date < today()

const load = async () => {
  loading.value = true
  try {
    const res = await getTodos({ page: page.value, page_size: 12, period_type: activePeriod.value, status: status.value || undefined, keyword: keyword.value.trim() || undefined })
    rows.value = res.data.items
    total.value = res.data.total
  } finally { loading.value = false }
}
const loadSummary = async () => Object.assign(summary, (await getTodoSummary()).data)
const refresh = () => Promise.all([load(), loadSummary()])
let searchTimer: ReturnType<typeof setTimeout>
watch([activePeriod, status], () => { page.value = 1; load() })
watch(keyword, () => { page.value = 1; clearTimeout(searchTimer); searchTimer = setTimeout(load, 300) })
onMounted(refresh)

const openCreate = async () => {
  editingId.value = null
  Object.assign(form, { title: '', description: '', period_type: activePeriod.value, scheduled_date: today(), priority: 'medium', status: 'pending' })
  dialogVisible.value = true
  await nextTick()
  formRef.value?.clearValidate()
}
const openEdit = async (row: Todo) => {
  editingId.value = row.id
  Object.assign(form, { title: row.title, description: row.description || '', period_type: row.period_type, scheduled_date: row.scheduled_date, priority: row.priority, status: row.status })
  dialogVisible.value = true
  await nextTick()
  formRef.value?.clearValidate()
}
const submit = async () => {
  if (!formRef.value || !(await formRef.value.validate())) return
  submitting.value = true
  try {
    const payload = { ...form, title: form.title.trim(), description: form.description?.trim() || null }
    if (editingId.value) await updateTodo(editingId.value, payload)
    else await createTodo(payload)
    activePeriod.value = form.period_type
    dialogVisible.value = false
    ElMessage.success(editingId.value ? '待办已更新' : '待办已创建')
    await refresh()
  } finally { submitting.value = false }
}
const toggle = async (row: Todo) => {
  togglingId.value = row.id
  try {
    await updateTodo(row.id, { status: row.status === 'completed' ? 'pending' : 'completed' })
    ElMessage.success(row.status === 'completed' ? '已恢复为待完成' : '做得漂亮，已完成')
    await refresh()
  } finally { togglingId.value = null }
}
const remove = async (id: number) => { await deleteTodo(id); ElMessage.success('待办已删除'); await refresh() }
</script>

<template>
  <div class="page-enter todo-page">
    <div class="page-heading todo-heading">
      <div><span class="kicker">RHYTHM PLANNER</span><h2>待办事项</h2><p>把目标放进合适的时间尺度，今天就从最重要的一件开始。</p></div>
      <el-button type="primary" :icon="Plus" size="large" @click="openCreate">新增待办</el-button>
    </div>

    <section class="todo-overview">
      <div class="progress-orbit" :style="completionStyle"><div><strong>{{ summary.completion_rate }}%</strong><span>总体完成率</span></div></div>
      <div class="overview-copy"><span class="overview-label">FOCUS SNAPSHOT</span><h3>还有 {{ summary.pending }} 件事值得投入</h3><p>已完成 {{ summary.completed }} 项，共记录 {{ summary.total }} 项计划。</p></div>
      <div class="overview-stats"><div><span>待完成</span><strong>{{ summary.pending }}</strong></div><div><span>已逾期</span><strong class="danger">{{ summary.overdue }}</strong></div><div><span>已完成</span><strong>{{ summary.completed }}</strong></div></div>
    </section>

    <nav class="period-switcher" aria-label="待办周期">
      <button v-for="item in periods" :key="item.value" :class="{ active: activePeriod === item.value }" @click="activePeriod = item.value">
        <span>{{ item.english }}</span><strong>{{ item.label }}</strong><em>{{ periodCount(item.value) }}</em>
      </button>
    </nav>

    <section class="panel todo-panel">
      <div class="todo-toolbar">
        <div><span class="section-index">0{{ periods.findIndex(item => item.value === activePeriod) + 1 }}</span><div><h3>{{ currentLabel }}</h3><p>按计划日期与优先级排列</p></div></div>
        <div class="todo-filters"><el-input v-model="keyword" :prefix-icon="Search" placeholder="搜索待办或备注" clearable /><el-select v-model="status" placeholder="全部状态"><el-option label="全部状态" value="" /><el-option label="待完成" value="pending" /><el-option label="已完成" value="completed" /></el-select></div>
      </div>

      <div v-loading="loading" class="todo-list">
        <article v-for="row in rows" :key="row.id" class="todo-item" :class="{ completed: row.status === 'completed', overdue: isOverdue(row) }">
          <button class="check-button" :class="{ checked: row.status === 'completed' }" :aria-label="row.status === 'completed' ? '恢复待办' : '完成待办'" :disabled="togglingId === row.id" @click="toggle(row)"><el-icon v-if="row.status === 'completed'"><Check /></el-icon></button>
          <div class="todo-main"><div class="todo-title-row"><h4>{{ row.title }}</h4><span class="priority" :class="row.priority">{{ priorityText[row.priority] }}</span></div><p v-if="row.description">{{ row.description }}</p><div class="todo-meta"><span><el-icon><Calendar /></el-icon>{{ friendlyDate(row.scheduled_date) }} · {{ row.scheduled_date }}</span><span><el-icon><Clock /></el-icon>{{ periodText[row.period_type] }}计划</span><span v-if="isOverdue(row)" class="overdue-label">已逾期</span></div></div>
          <div class="todo-actions"><button aria-label="修改待办" @click="openEdit(row)"><el-icon><Edit /></el-icon></button><el-popconfirm title="确认删除这项待办吗？" @confirm="remove(row.id)"><template #reference><button class="delete" aria-label="删除待办"><el-icon><Delete /></el-icon></button></template></el-popconfirm></div>
        </article>
        <div v-if="!loading && !rows.length" class="todo-empty"><div><Check /></div><h4>这里很清爽</h4><p>当前没有{{ currentLabel }}，新建一项计划开始行动吧。</p><el-button :icon="Plus" @click="openCreate">新建待办</el-button></div>
      </div>
      <div v-if="total > 12" class="pagination"><el-pagination v-model:current-page="page" layout="total, prev, pager, next" :page-size="12" :total="total" @current-change="load" /></div>
    </section>

    <el-dialog v-model="dialogVisible" class="order-dialog" :modal-class="`order-dialog-overlay ${appStore.sidebarCollapsed ? 'is-sidebar-collapsed' : ''}`" width="620px" align-center append-to-body destroy-on-close :close-on-click-modal="false">
      <template #header><div class="dialog-heading"><span>{{ editingId ? 'EDIT TODO' : 'NEW TODO' }}</span><h3>{{ editingId ? '修改待办事项' : '创建一个新计划' }}</h3></div></template>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="待办标题" prop="title"><el-input v-model="form.title" maxlength="120" show-word-limit placeholder="明确写下需要完成的事情" /></el-form-item>
        <div class="todo-form-grid"><el-form-item label="待办周期" prop="period_type"><el-segmented v-model="form.period_type" :options="[{ label: '每日', value: 'daily' }, { label: '每周', value: 'weekly' }, { label: '每月', value: 'monthly' }]" /></el-form-item><el-form-item label="计划日期" prop="scheduled_date"><el-date-picker v-model="form.scheduled_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" /></el-form-item><el-form-item label="优先级" prop="priority"><el-select v-model="form.priority"><el-option label="高优先级" value="high" /><el-option label="中优先级" value="medium" /><el-option label="低优先级" value="low" /></el-select></el-form-item><el-form-item v-if="editingId" label="完成状态" prop="status"><el-select v-model="form.status"><el-option label="待完成" value="pending" /><el-option label="已完成" value="completed" /></el-select></el-form-item></div>
        <el-form-item label="备注"><el-input v-model="form.description" type="textarea" :rows="4" maxlength="1000" show-word-limit placeholder="补充上下文、验收标准或下一步行动" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="submitting" @click="submit">保存待办</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.todo-page{display:flex;flex-direction:column;gap:20px}.todo-heading{margin-bottom:0}.todo-overview{position:relative;display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:28px;min-height:166px;padding:28px 34px;overflow:hidden;border-radius:20px;color:#f4fff9;background:radial-gradient(circle at 82% -60%,rgba(217,246,95,.28),transparent 46%),linear-gradient(120deg,#102822,#184a3b);box-shadow:0 20px 50px rgba(16,40,34,.15)}.todo-overview:after{position:absolute;right:-35px;bottom:-70px;width:210px;height:130px;border:1px solid rgba(217,246,95,.2);border-radius:50%;content:'';transform:rotate(-18deg)}.progress-orbit{display:grid;width:108px;height:108px;padding:7px;place-items:center;border-radius:50%;background:conic-gradient(#d9f65f var(--progress),rgba(255,255,255,.12) 0);transition:background .5s}.progress-orbit>div{display:flex;width:94px;height:94px;align-items:center;justify-content:center;flex-direction:column;border-radius:50%;background:#15392f}.progress-orbit strong{font-size:25px}.progress-orbit span{margin-top:3px;color:#94b5aa;font-size:10px}.overview-label{color:#b7d95e;font-size:9px;letter-spacing:2px}.overview-copy h3{margin:7px 0 5px;font-size:23px}.overview-copy p{color:#92aea5;font-size:12px}.overview-stats{z-index:1;display:flex}.overview-stats>div{min-width:92px;padding:8px 22px;border-left:1px solid rgba(255,255,255,.11)}.overview-stats span{display:block;color:#8ca99f;font-size:10px}.overview-stats strong{display:block;margin-top:5px;font-size:23px}.overview-stats .danger{color:#ff937e}.period-switcher{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.period-switcher button{position:relative;display:flex;align-items:center;gap:14px;padding:17px 20px;border:1px solid var(--line);border-radius:14px;color:#7b8581;background:rgba(255,254,250,.65);transition:.2s}.period-switcher button:hover{border-color:#b9c9c1;transform:translateY(-1px)}.period-switcher button.active{border-color:#1a7458;color:#173b30;background:#fffefa;box-shadow:0 8px 24px rgba(26,84,65,.08)}.period-switcher button.active:after{position:absolute;right:17px;bottom:-1px;left:17px;height:3px;border-radius:3px;background:#1aa573;content:''}.period-switcher span{font-size:9px;letter-spacing:1.5px}.period-switcher strong{font-size:14px}.period-switcher em{margin-left:auto;font-style:normal;font-weight:700}.todo-panel{overflow:hidden}.todo-toolbar{display:flex;align-items:center;justify-content:space-between;padding:20px 22px;border-bottom:1px solid var(--line)}.todo-toolbar>div:first-child{display:flex;align-items:center;gap:13px}.section-index{color:#aed632;font:800 24px Manrope}.todo-toolbar h3{font-size:15px}.todo-toolbar p{margin-top:2px;color:var(--muted);font-size:10px}.todo-filters{display:grid;grid-template-columns:220px 130px;gap:10px}.todo-list{min-height:300px}.todo-item{display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:flex-start;gap:16px;padding:20px 24px;border-bottom:1px solid #ecece5;transition:.2s}.todo-item:hover{background:#fbfcf7}.todo-item.completed{opacity:.62}.todo-item.completed h4{text-decoration:line-through}.todo-item.overdue{box-shadow:inset 3px 0 #e36a55}.check-button{display:grid;width:23px;height:23px;margin:0;padding:0;place-items:center;border:1.5px solid #b8c4bf;border-radius:7px;color:#153b2f;background:white}.check-button:hover{border-color:#159c6d}.check-button.checked{border-color:#159c6d;color:white;background:#159c6d}.todo-title-row{display:flex;min-height:23px;align-items:center;gap:9px}.todo-main h4{margin:0;font-size:14px;line-height:23px}.todo-main>p{max-width:760px;margin-top:3px;overflow:hidden;color:#727d78;font-size:12px;line-height:1.45;text-overflow:ellipsis;white-space:nowrap}.priority{padding:3px 7px;border-radius:20px;font-size:9px}.priority.high{color:#bc503f;background:#ffebe7}.priority.medium{color:#9a6a11;background:#fff4d7}.priority.low{color:#487063;background:#eaf4f0}.todo-meta{display:flex;gap:16px;margin-top:7px}.todo-meta span{display:inline-flex;align-items:center;gap:4px;color:#929b97;font-size:10px}.todo-meta .overdue-label{color:#d85c49}.todo-actions{display:flex;gap:5px}.todo-actions button{display:grid;width:31px;height:31px;padding:0;place-items:center;border:0;border-radius:8px;color:#26745b;background:#edf7f2}.todo-actions button.delete{color:#bd5549;background:#fff0ed}.todo-empty{display:flex;min-height:340px;align-items:center;justify-content:center;flex-direction:column;color:#89938e;text-align:center}.todo-empty>div{display:grid;width:54px;height:54px;margin-bottom:12px;place-items:center;border-radius:50%;color:#55a486;background:#eaf5ef}.todo-empty svg{width:24px}.todo-empty h4{color:#34483f}.todo-empty p{margin:6px 0 15px;font-size:12px}.pagination{display:flex;justify-content:flex-end;padding:16px 20px}.todo-form-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 18px}.todo-form-grid :deep(.el-date-editor),.todo-form-grid :deep(.el-select),.todo-form-grid :deep(.el-segmented){width:100%}
@media(max-width:1000px){.todo-overview{grid-template-columns:auto 1fr}.overview-stats{grid-column:1/-1}.overview-stats>div:first-child{border-left:0;padding-left:0}.todo-toolbar{align-items:flex-start;gap:15px;flex-direction:column}.todo-filters{width:100%;grid-template-columns:1fr 150px}}
@media(max-width:700px){.todo-overview{grid-template-columns:1fr;padding:25px}.progress-orbit{width:92px;height:92px}.progress-orbit>div{width:78px;height:78px}.overview-stats>div{min-width:0;flex:1;padding:8px 12px}.period-switcher{grid-template-columns:1fr}.todo-filters,.todo-form-grid{grid-template-columns:1fr}.todo-item{padding:18px 15px}.todo-main>p{white-space:normal}.todo-meta{gap:8px;flex-wrap:wrap}.todo-actions{flex-direction:column}}
</style>
