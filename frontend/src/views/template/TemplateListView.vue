<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Check, CopyDocument, Delete, Edit, FolderOpened, Plus, Refresh, Search, TopRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useAppStore } from '@/stores/app'
import {
  TEMPLATE_FORMATS,
  createTemplate,
  deleteTemplate,
  getTemplates,
  updateTemplate,
  type TemplateFormat,
  type TemplatePayload,
  type TemplateRecord,
} from '@/api/templates'

const appStore = useAppStore()
const rows = ref<TemplateRecord[]>([])
const loading = ref(false)
const keyword = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const dialogVisible = ref(false)
const submitting = ref(false)
const deletingId = ref<number | null>(null)
const editingId = ref<number | null>(null)
const activeFormat = ref<TemplateFormat>('Html')
const formRef = ref<FormInstance>()

const emptyForm = () => ({
  name: '',
  notes: '',
  figma_share: '',
  psd_share: '',
  xd_share: '',
  jsd_share: '',
  html_share: '',
  material_share: '',
})
const form = reactive(emptyForm())
const filledCount = computed(() => TEMPLATE_FORMATS.filter(item => form[item.field].trim()).length)
const rules: FormRules = {
  name: [
    { required: true, whitespace: true, message: '请输入模板名称', trigger: 'blur' },
    { max: 100, message: '模板名称最多 100 个字符', trigger: 'blur' },
  ],
}

let requestVersion = 0
let filterTimer: ReturnType<typeof setTimeout> | undefined
let disposed = false

const loadTemplates = async () => {
  clearTimeout(filterTimer)
  const version = ++requestVersion
  loading.value = true
  try {
    const result = await getTemplates({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value.trim() || undefined,
    })
    if (disposed || version !== requestVersion) return
    rows.value = result.data.items
    total.value = result.data.total
    // A deletion in another session may leave the current page empty.
    if (!rows.value.length && page.value > 1) {
      page.value = Math.max(1, result.data.total_pages)
      await loadTemplates()
    }
  } catch {
    // The shared request interceptor displays API errors.
  } finally {
    if (!disposed && version === requestVersion) loading.value = false
  }
}

watch(keyword, () => {
  ++requestVersion
  clearTimeout(filterTimer)
  filterTimer = setTimeout(() => {
    page.value = 1
    loadTemplates()
  }, 300)
})

const resetFilters = () => {
  keyword.value = ''
  page.value = 1
  nextTick(loadTemplates)
}

const changePageSize = () => {
  page.value = 1
  loadTemplates()
}

onMounted(loadTemplates)
onBeforeUnmount(() => {
  disposed = true
  ++requestVersion
  clearTimeout(filterTimer)
})

const openCreate = async () => {
  editingId.value = null
  Object.assign(form, emptyForm())
  activeFormat.value = 'Html'
  dialogVisible.value = true
  await nextTick()
  formRef.value?.clearValidate()
}

const openEdit = async (row: TemplateRecord) => {
  editingId.value = row.id
  Object.assign(form, emptyForm(), { name: row.name, notes: row.notes || '' })
  for (const item of TEMPLATE_FORMATS) form[item.field] = row[item.field] || ''
  activeFormat.value = TEMPLATE_FORMATS.find(item => row[item.field])?.value || 'Html'
  dialogVisible.value = true
  await nextTick()
  formRef.value?.clearValidate()
}

const submit = async () => {
  if (submitting.value || !formRef.value || !(await formRef.value.validate().catch(() => false))) return
  if (!filledCount.value) {
    ElMessage.warning('请至少填写一项分享内容')
    return
  }
  const payload: TemplatePayload = { ...form, name: form.name.trim(), notes: form.notes.trim() || null }
  for (const item of TEMPLATE_FORMATS) payload[item.field] = form[item.field].trim() || null
  submitting.value = true
  try {
    if (editingId.value !== null) {
      await updateTemplate(editingId.value, payload)
      ElMessage.success('模板修改成功')
    } else {
      await createTemplate(payload)
      ElMessage.success('模板新增成功')
    }
    dialogVisible.value = false
    page.value = 1
    await loadTemplates()
  } catch {
    // Keep the form open so entered share text can be corrected or retried.
  } finally {
    submitting.value = false
  }
}

const remove = async (row: TemplateRecord) => {
  if (deletingId.value !== null) return
  deletingId.value = row.id
  try {
    await deleteTemplate(row.id)
    ElMessage.success('模板删除成功')
    if (rows.value.length === 1 && page.value > 1) page.value -= 1
    await loadTemplates()
  } catch {
    // The shared request interceptor displays API errors.
  } finally {
    deletingId.value = null
  }
}

const copyShare = async (content: string) => {
  try {
    if (!navigator.clipboard?.writeText) throw new Error('Clipboard API unavailable')
    await navigator.clipboard.writeText(content)
  } catch {
    // Clipboard API requires HTTPS; retain copying on local HTTP deployments.
    const previousFocus = document.activeElement as HTMLElement | null
    const input = document.createElement('textarea')
    input.value = content
    input.style.cssText = 'position:fixed;left:-9999px;top:0;'
    input.setAttribute('aria-label', '复制分享内容')
    document.body.appendChild(input)
    input.select()
    let copied = false
    try {
      copied = document.execCommand('copy')
    } catch {
      copied = false
    } finally {
      input.remove()
      previousFocus?.focus()
    }
    if (!copied) {
      ElMessage.error('复制失败，请点击“已提供”查看并手动复制分享内容')
      return
    }
  }
  ElMessage.success('分享内容已完整复制')
}

const dateFormatter = new Intl.DateTimeFormat('zh-CN', {
  timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', hour12: false,
})
const formatTime = (value: string) => dateFormatter.format(new Date(value)).replace(/\//g, '-')
const beforeClose = (done: () => void) => { if (!submitting.value) done() }
</script>

<template>
  <div class="page-enter template-page">
    <div class="page-heading">
      <div>
        <span class="kicker">TEMPLATE LIBRARY</span>
        <h2>模板管理</h2>
        <p>集中管理模板文件与素材的网盘分享内容，随时复制与打开。</p>
      </div>
      <el-button type="primary" :icon="Plus" size="large" @click="openCreate">新增模板</el-button>
    </div>

    <section class="panel resource-panel template-panel">
      <div class="toolbar template-toolbar">
        <el-input v-model="keyword" :prefix-icon="Search" placeholder="搜索模板名称或备注" maxlength="100" clearable
          aria-label="搜索模板名称或备注" @keyup.enter="page = 1; loadTemplates()" />
        <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
        <span class="template-result-count">{{ keyword.trim() ? '找到' : '共' }} <strong>{{ total }}</strong> 个模板</span>
      </div>

      <el-table v-loading="loading" :data="rows" row-key="id">
        <el-table-column label="模板" min-width="190">
          <template #default="scope">
            <div class="template-name-cell">
              <strong :title="scope.row.name">{{ scope.row.name }}</strong>
              <span v-if="scope.row.notes" :title="scope.row.notes">{{ scope.row.notes }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column v-for="item in TEMPLATE_FORMATS" :key="item.value" :label="item.value" min-width="114">
          <template #header>
            <div class="template-format-heading"><strong>{{ item.value }}</strong><span>{{ item.description }}</span></div>
          </template>
          <template #default="scope">
            <div v-if="scope.row[item.field]" class="template-share-cell">
              <el-popover trigger="click" placement="top" :width="320">
                <template #reference>
                  <button class="template-share-status" :aria-label="`查看${scope.row.name}的${item.value}分享内容`">
                    <i></i>已提供
                  </button>
                </template>
                <div class="template-share-preview"><strong>{{ scope.row.name }} · {{ item.value }}</strong><p>{{ scope.row[item.field] }}</p></div>
              </el-popover>
              <div class="template-share-actions">
                <button :aria-label="`复制${scope.row.name}的${item.value}分享内容`" @click="copyShare(scope.row[item.field])">
                  <el-icon><CopyDocument /></el-icon>复制
                </button>
                <a v-if="scope.row.share_urls[item.value]" :href="scope.row.share_urls[item.value]" target="_blank" rel="noopener noreferrer"
                  :aria-label="`打开${scope.row.name}的${item.value}网盘链接`"><el-icon><TopRight /></el-icon>打开</a>
              </div>
            </div>
            <span v-else class="template-share-empty">未提供</span>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="148">
          <template #default="scope"><span class="template-update-time">{{ formatTime(scope.row.updated_at) }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right" align="center">
          <template #default="scope">
            <div class="order-row-actions">
              <button class="order-icon-action edit" :aria-label="`修改模板${scope.row.name}`" title="修改模板" @click="openEdit(scope.row)"><el-icon><Edit /></el-icon></button>
              <el-popconfirm :title="`确认删除模板“${scope.row.name}”吗？`" confirm-button-text="删除" cancel-button-text="取消" :width="260" @confirm="remove(scope.row)">
                <template #reference><button class="order-icon-action remove" :aria-label="`删除模板${scope.row.name}`" title="删除模板" :disabled="deletingId !== null"><el-icon><Delete /></el-icon></button></template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <div class="template-empty">
            <div class="template-empty-icon"><el-icon><FolderOpened /></el-icon></div>
            <strong>{{ keyword.trim() ? '没有找到匹配的模板' : '还没有模板' }}</strong>
            <p>{{ keyword.trim() ? '试试其他名称，或重置搜索条件。' : '新增第一个模板，把各个格式的分享内容整理在一起。' }}</p>
            <el-button v-if="!keyword.trim()" :icon="Plus" @click="openCreate">新增模板</el-button>
          </div>
        </template>
      </el-table>

      <div class="pagination template-pagination">
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next" :total="total" @current-change="loadTemplates" @size-change="changePageSize" />
      </div>
    </section>

    <el-dialog v-model="dialogVisible" class="order-dialog template-dialog"
      :modal-class="`order-dialog-overlay ${appStore.sidebarCollapsed ? 'is-sidebar-collapsed' : ''}`"
      width="680px" align-center append-to-body destroy-on-close :close-on-click-modal="false"
      :close-on-press-escape="!submitting" :show-close="!submitting" :before-close="beforeClose">
      <template #header>
        <div class="dialog-heading"><span>{{ editingId !== null ? 'EDIT TEMPLATE' : 'NEW TEMPLATE' }}</span><h3>{{ editingId !== null ? '修改模板' : '新增模板' }}</h3><p>链接与提取码一起粘贴，分享文案完整保存。</p></div>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" :disabled="submitting" @submit.prevent="submit">
        <el-form-item label="模板名称" prop="name"><el-input v-model="form.name" maxlength="100" show-word-limit placeholder="例如：云肩" /></el-form-item>

        <div class="template-shares-heading"><strong>文件与素材分享内容 <em>*</em></strong><span>已填写 {{ filledCount }} / {{ TEMPLATE_FORMATS.length }}</span></div>
        <p class="template-shares-hint">至少填写一项分享内容，其他项可以后续补充。</p>
        <el-tabs v-model="activeFormat" class="template-format-tabs">
          <el-tab-pane v-for="item in TEMPLATE_FORMATS" :key="item.value" :name="item.value">
            <template #label><span class="template-tab-label">{{ item.value }}<el-icon v-if="form[item.field].trim()"><Check /></el-icon></span></template>
            <el-form-item :label="`${item.value} · ${item.description}`" :prop="item.field">
              <el-input v-model="form[item.field]" type="textarea" :rows="5" maxlength="2000" show-word-limit
                :placeholder="`粘贴${item.value === 'Html' ? '源代码' : item.value === 'Jsd' ? '即时设计' : item.value}的完整网盘分享内容，例如：\n通过网盘分享的文件：云肩-${item.description}\n链接: https://pan.baidu.com/s/…?pwd=abcd\n提取码: abcd`" />
            </el-form-item>
          </el-tab-pane>
        </el-tabs>
        <el-form-item label="备注" prop="notes"><el-input v-model="form.notes" type="textarea" :rows="2" maxlength="1000" show-word-limit placeholder="选填，补充模板说明或使用注意事项" /></el-form-item>
      </el-form>
      <template #footer><el-button :disabled="submitting" @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="submitting" @click="submit">{{ editingId !== null ? '保存修改' : '确认新增' }}</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.template-toolbar { align-items: center; }
.template-panel :deep(.el-table__cell.is-fixed-column--right) { background: var(--surface); }
.template-panel :deep(.el-table__body tr:hover .el-table__cell.is-fixed-column--right) { background: #f8faf7; }
.template-result-count { margin-left: auto; color: var(--muted); font-size: 12px; white-space: nowrap; }
.template-result-count strong { margin: 0 3px; color: var(--green-900); }
.template-name-cell { display: flex; min-width: 0; flex-direction: column; gap: 5px; padding: 8px 0; }
.template-name-cell strong { overflow: hidden; color: var(--green-900); font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.template-name-cell > span { overflow: hidden; color: var(--muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.template-format-heading { display: flex; flex-direction: column; gap: 1px; padding: 3px 0; }
.template-format-heading strong { color: #4a6056; font-size: 12px; }
.template-format-heading > span { color: var(--muted); font-size: 10px; font-weight: 400; }
.template-share-cell { display: flex; flex-direction: column; align-items: flex-start; gap: 3px; padding: 5px 0; }
.template-share-status { display: inline-flex; align-items: center; gap: 5px; padding: 0; border: 0; color: #398365; background: transparent; font-size: 10px; line-height: 20px; }
.template-share-status i { width: 5px; height: 5px; border-radius: 50%; background: var(--green-600); }
.template-share-actions { display: flex; align-items: center; gap: 9px; }
.template-share-actions button, .template-share-actions a { display: inline-flex; align-items: center; gap: 3px; padding: 0; border: 0; color: #506c60; background: transparent; font-size: 11px; line-height: 23px; text-decoration: none; white-space: nowrap; }
.template-share-actions button:hover, .template-share-actions a:hover { color: var(--green-600); }
.template-share-actions .el-icon { font-size: 12px; }
.template-share-status:focus-visible, .template-share-actions button:focus-visible, .template-share-actions a:focus-visible { border-radius: 3px; outline: 2px solid var(--green-600); outline-offset: 3px; }
.template-share-empty { color: #a0a8a3; font-size: 11px; }
.template-update-time { color: var(--muted); font-size: 11px; white-space: nowrap; }
.template-share-preview > strong { color: var(--green-900); font-size: 12px; }
.template-share-preview > p { max-height: 240px; margin-top: 9px; overflow-y: auto; color: #52645b; font-size: 12px; line-height: 1.7; overflow-wrap: anywhere; white-space: pre-wrap; }
.template-empty { display: flex; min-height: 280px; flex-direction: column; align-items: center; justify-content: center; padding: 24px 12px; line-height: 1.6; }
.template-empty-icon { display: grid; width: 52px; height: 52px; margin-bottom: 13px; place-items: center; border: 1px solid #dfe9df; border-radius: 15px; color: #558f75; background: #f0f6ed; font-size: 25px; }
.template-empty > strong { color: #3b5246; font-size: 14px; }
.template-empty > p { margin: 6px 0 17px; color: var(--muted); font-size: 12px; }
.template-pagination { justify-content: flex-end; }
.template-shares-heading { display: flex; align-items: center; justify-content: space-between; margin-top: 20px; }
.template-shares-heading strong { color: #344b43; font-size: 13px; }
.template-shares-heading em { color: var(--el-color-danger); font-style: normal; }
.template-shares-heading > span { color: var(--green-600); font-size: 11px; }
.template-shares-hint { margin: 6px 0 0; color: var(--muted); font-size: 11px; }
.template-tab-label { display: inline-flex; align-items: center; gap: 4px; }
.template-tab-label .el-icon { color: var(--green-600); font-size: 12px; }
.template-format-tabs :deep(.el-tabs__item) { font-size: 12px; }
.template-format-tabs :deep(.el-tabs__nav-wrap::after) { height: 1px; background: var(--line); }
.template-format-tabs :deep(.el-tabs__active-bar) { background: var(--green-600); }
.template-format-tabs :deep(.el-tabs__item.is-active) { color: var(--green-600); }
.template-format-tabs :deep(.el-textarea__inner) { line-height: 1.7; }
:global(.template-dialog .el-dialog__body) { padding-top: 18px; padding-bottom: 12px; overflow-y: auto; }
:global(.template-dialog .el-form-item) { margin-bottom: 17px; }
:global(.template-dialog .el-dialog__header) { padding-top: 18px; padding-bottom: 15px; }
@media (max-width: 700px) {
  .template-panel { padding: 14px; }
  .template-toolbar { flex-wrap: wrap; }
  .template-toolbar .el-input { flex: 1; min-width: 180px; }
  .template-result-count { flex-basis: 100%; margin-left: 0; }
  .template-pagination { overflow-x: auto; justify-content: flex-start; }
  .template-format-tabs :deep(.el-tabs__item) { padding: 0 14px; }
}
</style>
