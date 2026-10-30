<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { CopyDocument, Delete, Edit, Link, Plus, Refresh, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useAppStore } from '@/stores/app'
import { copyText } from '@/utils/clipboard'
import {
  createXianyuLink,
  deleteXianyuLink,
  getXianyuLinks,
  updateXianyuLink,
  type XianyuLink,
} from '@/api/xianyuLinks'

const appStore = useAppStore()
const rows = ref<XianyuLink[]>([])
const loading = ref(false)
const keyword = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const dialogVisible = ref(false)
const submitting = ref(false)
const deletingId = ref<number | null>(null)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const form = reactive({ title: '', link: '' })

const getLinkUrl = (value: string) => {
  const link = value.match(/https?:\/\/[^\s<>"'「」【】()[\]，。；！？]+/i)?.[0]
  if (!link) return undefined
  try {
    const url = new URL(link)
    return /^https?:\/\/[^/]/i.test(link)
      && ['http:', 'https:'].includes(url.protocol)
      && !url.username && !url.password
      && !link.includes('\\')
      && !Array.from(link).some(char => /\s/.test(char) || char.charCodeAt(0) < 32)
      ? link : undefined
  } catch {
    return undefined
  }
}

const rules: FormRules = {
  title: [
    { required: true, whitespace: true, message: '请输入闲鱼标题', trigger: 'blur' },
    { max: 200, message: '闲鱼标题最多 200 个字符', trigger: 'blur' },
  ],
  link: [
    { required: true, whitespace: true, message: '请输入闲鱼链接', trigger: 'blur' },
    { max: 2000, message: '闲鱼链接最多 2000 个字符', trigger: 'blur' },
  ],
}

let requestVersion = 0
let filterTimer: ReturnType<typeof setTimeout> | undefined
let disposed = false

const loadLinks = async () => {
  clearTimeout(filterTimer)
  const version = ++requestVersion
  loading.value = true
  try {
    const result = await getXianyuLinks({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value.trim() || undefined,
    })
    if (disposed || version !== requestVersion) return
    rows.value = result.data.items
    total.value = result.data.total
    if (!rows.value.length && page.value > 1) {
      page.value = Math.max(1, result.data.total_pages)
      await loadLinks()
    }
  } catch {
    // API errors are displayed by the shared request interceptor.
  } finally {
    if (!disposed && version === requestVersion) loading.value = false
  }
}

const search = () => {
  page.value = 1
  return loadLinks()
}
const resetFilters = async () => {
  keyword.value = ''
  await nextTick()
  await search()
}

watch(keyword, () => {
  ++requestVersion
  clearTimeout(filterTimer)
  filterTimer = setTimeout(search, 300)
})
onMounted(loadLinks)
onBeforeUnmount(() => {
  disposed = true
  ++requestVersion
  clearTimeout(filterTimer)
})

const openCreate = async () => {
  editingId.value = null
  Object.assign(form, { title: '', link: '' })
  dialogVisible.value = true
  await nextTick()
  formRef.value?.clearValidate()
}
const openEdit = async (row: XianyuLink) => {
  editingId.value = row.id
  Object.assign(form, { title: row.title, link: row.link })
  dialogVisible.value = true
  await nextTick()
  formRef.value?.clearValidate()
}
const submit = async () => {
  if (submitting.value || !formRef.value || !(await formRef.value.validate().catch(() => false))) return
  submitting.value = true
  try {
    const payload = { title: form.title.trim(), link: form.link.trim() }
    if (editingId.value !== null) {
      await updateXianyuLink(editingId.value, payload)
      ElMessage.success('闲鱼链接修改成功')
    } else {
      await createXianyuLink(payload)
      ElMessage.success('闲鱼链接新增成功')
    }
    dialogVisible.value = false
    page.value = 1
    await loadLinks()
  } catch {
    // Preserve entered values for correction or retry.
  } finally {
    submitting.value = false
  }
}
const remove = async (row: XianyuLink) => {
  if (deletingId.value !== null) return
  deletingId.value = row.id
  try {
    await deleteXianyuLink(row.id)
    ElMessage.success('闲鱼链接删除成功')
    if (rows.value.length === 1 && page.value > 1) page.value -= 1
    await loadLinks()
  } catch {
    // API errors are displayed by the shared request interceptor.
  } finally {
    deletingId.value = null
  }
}
const copyLink = async (row: XianyuLink) => {
  try {
    await copyText(row.link)
    ElMessage.success('闲鱼链接已复制')
  } catch {
    ElMessage.error('复制失败，请手动选中链接复制')
  }
}
const beforeClose = (done: () => void) => { if (!submitting.value) done() }
const dateFormatter = new Intl.DateTimeFormat('zh-CN', {
  timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', hour12: false,
})
const formatTime = (value: string) => dateFormatter.format(new Date(value)).replace(/\//g, '-')
</script>

<template>
  <div class="page-enter xianyu-page">
    <div class="page-heading">
      <div>
        <span class="kicker">XIANYU LINKS</span>
        <h2>闲鱼链接</h2>
        <p>集中整理闲鱼标题与链接，一键复制，随时取用。</p>
      </div>
      <el-button type="primary" :icon="Plus" size="large" @click="openCreate">新增链接</el-button>
    </div>

    <section class="panel resource-panel xianyu-panel">
      <div class="toolbar xianyu-toolbar">
        <el-input v-model="keyword" :prefix-icon="Search" placeholder="搜索闲鱼标题或链接" aria-label="搜索闲鱼标题或链接"
          maxlength="200" clearable @keyup.enter="search" />
        <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
        <span class="xianyu-result-count">{{ keyword.trim() ? '找到' : '共' }} <strong>{{ total }}</strong> 条链接</span>
      </div>

      <el-table v-loading="loading" :data="rows" row-key="id">
        <el-table-column prop="title" label="闲鱼标题" min-width="220" show-overflow-tooltip>
          <template #default="scope"><strong class="xianyu-title">{{ scope.row.title }}</strong></template>
        </el-table-column>
        <el-table-column prop="link" label="闲鱼链接" min-width="300">
          <template #default="scope">
            <a v-if="getLinkUrl(scope.row.link)" class="xianyu-url" :href="getLinkUrl(scope.row.link)" :title="scope.row.link" :aria-label="`打开${scope.row.title}的闲鱼链接`" target="_blank" rel="noopener noreferrer">{{ scope.row.link }}</a>
            <span v-else class="xianyu-url" :title="scope.row.link">{{ scope.row.link }}</span>
          </template>
        </el-table-column>
        <el-table-column label="复制" width="118">
          <template #default="scope"><el-button class="copy-link-button" :icon="CopyDocument" size="small" :aria-label="`复制${scope.row.title}的闲鱼链接`" @click="copyLink(scope.row)">复制链接</el-button></template>
        </el-table-column>
        <el-table-column label="更新时间" width="148">
          <template #default="scope"><span class="xianyu-update-time">{{ formatTime(scope.row.updated_at) }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right" align="center">
          <template #default="scope">
            <div class="order-row-actions">
              <button class="order-icon-action edit" :aria-label="`修改闲鱼链接${scope.row.title}`" title="修改闲鱼链接" @click="openEdit(scope.row)"><el-icon><Edit /></el-icon></button>
              <el-popconfirm :title="`确认删除“${scope.row.title}”的闲鱼链接吗？`" :width="260" confirm-button-text="删除" cancel-button-text="取消" @confirm="remove(scope.row)">
                <template #reference><button class="order-icon-action remove" :aria-label="`删除闲鱼链接${scope.row.title}`" title="删除闲鱼链接" :disabled="deletingId !== null"><el-icon><Delete /></el-icon></button></template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <div class="xianyu-empty">
            <div class="xianyu-empty-icon"><el-icon><Link /></el-icon></div>
            <strong>{{ keyword.trim() ? '没有找到匹配的闲鱼链接' : '还没有闲鱼链接' }}</strong>
            <p>{{ keyword.trim() ? '试试其他关键词，或重置搜索条件。' : '保存闲鱼标题和链接，需要分享时一键复制。' }}</p>
            <el-button v-if="!keyword.trim()" :icon="Plus" @click="openCreate">新增链接</el-button>
          </div>
        </template>
      </el-table>

      <div class="pagination xianyu-pagination">
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next" :total="total" @current-change="loadLinks" @size-change="search" />
      </div>
    </section>

    <el-dialog v-model="dialogVisible" class="order-dialog xianyu-dialog"
      :modal-class="`order-dialog-overlay ${appStore.sidebarCollapsed ? 'is-sidebar-collapsed' : ''}`"
      width="600px" align-center append-to-body destroy-on-close :close-on-click-modal="false"
      :close-on-press-escape="!submitting" :show-close="!submitting" :before-close="beforeClose">
      <template #header><div class="dialog-heading"><span>{{ editingId !== null ? 'EDIT XIANYU LINK' : 'NEW XIANYU LINK' }}</span><h3>{{ editingId !== null ? '修改闲鱼链接' : '新增闲鱼链接' }}</h3></div></template>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" :disabled="submitting" @submit.prevent="submit">
        <el-form-item label="闲鱼标题" prop="title"><el-input v-model="form.title" maxlength="200" show-word-limit placeholder="请输入便于查找的闲鱼标题" /></el-form-item>
        <el-form-item label="闲鱼链接" prop="link"><el-input v-model="form.link" type="textarea" :rows="4" maxlength="2000" show-word-limit :placeholder="'粘贴闲鱼链接或完整分享文案，例如：\n【闲鱼】https://m.tb.cn/h.j4M3WAA?tk=rlj8TC9Tio5 CZ001 「我在闲鱼发【网页设计】」\n点击链接直接打开'" /></el-form-item>
      </el-form>
      <template #footer><el-button :disabled="submitting" @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="submitting" @click="submit">{{ editingId !== null ? '保存修改' : '确认新增' }}</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.xianyu-toolbar { align-items: center; }
.xianyu-result-count { margin-left: auto; color: var(--muted); font-size: 12px; white-space: nowrap; }
.xianyu-result-count strong { margin: 0 3px; color: var(--green-900); }
.xianyu-panel :deep(td.el-table__cell) { height: 68px; }
.xianyu-panel :deep(.el-table__cell.el-table-fixed-column--right) { background: var(--surface); }
.xianyu-panel :deep(.el-table__body tr:hover .el-table__cell.el-table-fixed-column--right) { background: #f8faf7; }
.xianyu-title { color: var(--green-900); font-size: 13px; }
.xianyu-url { display: block; overflow: hidden; color: #4f7666; font-size: 12px; text-overflow: ellipsis; text-decoration: none; white-space: nowrap; }
a.xianyu-url:hover { color: var(--green-600); text-decoration: underline; }
.xianyu-url:focus-visible { border-radius: 3px; outline: 2px solid var(--green-600); outline-offset: -2px; }
.copy-link-button { --el-button-text-color: #386d57; --el-button-border-color: #d8e5db; --el-button-bg-color: #f5f9f2; --el-button-hover-text-color: var(--green-600); --el-button-hover-border-color: #a7cab5; --el-button-hover-bg-color: #edf6e8; }
.xianyu-update-time { color: var(--muted); font-size: 11px; white-space: nowrap; }
.xianyu-empty { display: flex; min-height: 280px; flex-direction: column; align-items: center; justify-content: center; padding: 24px 12px; line-height: 1.6; }
.xianyu-empty-icon { display: grid; width: 52px; height: 52px; margin-bottom: 13px; place-items: center; border: 1px solid #e8e1bb; border-radius: 15px; color: #8d7b3a; background: #faf7e9; font-size: 25px; }
.xianyu-empty > strong { color: #3b5246; font-size: 14px; }
.xianyu-empty > p { margin: 6px 0 17px; color: var(--muted); font-size: 12px; }
.xianyu-pagination { justify-content: flex-end; }
:global(.xianyu-dialog .el-dialog__body) { padding-top: 20px; padding-bottom: 10px; overflow-y: auto; }
:global(.xianyu-dialog .el-form-item) { margin-bottom: 20px; }
:global(.xianyu-dialog .el-textarea__inner) { overflow-wrap: anywhere; line-height: 1.7; }
@media (max-width: 700px) {
  .xianyu-panel { padding: 14px; }
  .xianyu-toolbar { flex-wrap: wrap; }
  .xianyu-toolbar .el-input { flex: 1; min-width: 180px; }
  .xianyu-result-count { flex-basis: 100%; margin-left: 0; }
  .xianyu-pagination { overflow-x: auto; justify-content: flex-start; }
}
</style>
