<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Check, Delete, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  createAccountField,
  createAccountRecord,
  deleteAccountField,
  deleteAccountRecord,
  getAccountData,
  updateAccountRecord,
  type AccountField,
  type AccountFieldType,
  type AccountRecord,
  type AccountSummary,
} from '@/api/accountData'

interface AccountRow { id: number; [key: string]: string | number }
const loading = ref(false)
const fields = ref<AccountField[]>([])
const records = ref<AccountRecord[]>([])
const rows = computed<AccountRow[]>(() => records.value.map((item) => ({ id: item.id, ...item.values })))
const summary = ref<AccountSummary>({
  account_count: 0,
  total_followers: 0,
  total_notes: 0,
  field_count: 0,
  updated_at: '',
})

const fieldPopoverVisible = ref(false)
const newField = reactive<{ label: string; type: AccountFieldType }>({ label: '', type: 'text' })
const lastUpdated = computed(() => summary.value.updated_at
  ? new Date(summary.value.updated_at).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    })
  : '--:--')

const loadData = async () => {
  loading.value = true
  try {
    const result = await getAccountData()
    fields.value = result.data.fields
    records.value = result.data.records
    summary.value = result.data.summary
  } finally {
    loading.value = false
  }
}

const addField = async () => {
  const label = newField.label.trim()
  if (!label) return ElMessage.warning('请输入字段名称')
  if (fields.value.some((field) => field.label === label)) return ElMessage.warning('该字段已存在')
  const result = await createAccountField({ label, type: newField.type })
  fields.value.push(result.data.field)
  records.value.forEach((record) => {
    record.values[result.data.field.key] = result.data.default_value
  })
  newField.label = ''
  newField.type = 'text'
  fieldPopoverVisible.value = false
  ElMessage.success(`字段“${label}”已添加`)
}

const removeField = async (field: AccountField) => {
  const result = await deleteAccountField(field.id)
  fields.value = fields.value.filter((item) => item.id !== field.id)
  records.value.forEach((record) => {
    delete record.values[field.key]
  })
  summary.value = result.data.summary
}

const addRow = async () => {
  const values: Record<string, string | number> = {}
  fields.value.forEach((field) => {
    values[field.key] = field.type === 'number' ? 0 : ''
  })
  values.account = '新账号'
  const result = await createAccountRecord(values)
  records.value.push(result.data.record)
  summary.value = result.data.summary
  ElMessage.success('账号新增成功')
}

const saveCell = async (id: number, key: string, value: string | number) => {
  try {
    const result = await updateAccountRecord(id, { [key]: value })
    const index = records.value.findIndex((item) => item.id === id)
    if (index !== -1) records.value[index] = result.data.record
    summary.value = result.data.summary
  } catch {
    await loadData()
  }
}

const removeRow = async (id: number) => {
  const result = await deleteAccountRecord(id)
  records.value = records.value.filter((row) => row.id !== id)
  summary.value = result.data.summary
}

onMounted(loadData)
</script>

<template>
  <div class="page-enter account-data-page">
    <div class="page-heading">
      <div><span class="kicker">CONTENT ACCOUNTS</span>
        <h2>账号数据</h2>
        <p>灵活维护账号指标，并按需要扩展新的数据字段。</p>
      </div>
      <div class="account-page-actions">
        <span class="data-saved"><el-icon>
            <Check />
          </el-icon>已更新 · {{ lastUpdated }}</span>
        <el-button type="primary" :icon="Plus" size="large" @click="addRow">新增账号</el-button>
      </div>
    </div>

    <section class="account-insights">
      <div><span>账号数量</span><strong>{{ summary.account_count }}</strong><small>ACCOUNTS</small></div>
      <div><span>粉丝总数</span><strong>{{ summary.total_followers.toLocaleString('zh-CN') }}</strong><small>FOLLOWERS</small></div>
      <div><span>发布笔记</span><strong>{{ summary.total_notes }}</strong><small>NOTES</small></div>
    </section>

    <section class="panel account-table-panel">
      <div class="account-table-heading">
        <div>
          <h3>账号明细</h3>
        </div>
        <el-popover v-model:visible="fieldPopoverVisible" placement="bottom-end" :width="300" trigger="click">
          <template #reference><el-button :icon="Plus">新增字段</el-button></template>
          <div class="field-creator"><strong>添加表格字段</strong>
            <p>新字段会立即添加到所有账号行。</p><el-input v-model="newField.label" maxlength="20" placeholder="字段名称，如：获赞数"
              @keyup.enter="addField" /><el-select v-model="newField.type"><el-option label="文本"
                value="text" /><el-option label="数字" value="number" /></el-select><el-button type="primary"
              @click="addField">确认添加</el-button>
          </div>
        </el-popover>
      </div>

      <el-table v-loading="loading" :data="rows" row-key="id" empty-text="暂无账号数据">
        <el-table-column v-for="field in fields" :key="field.key" :min-width="field.key === 'account' ? 210 : 150">
          <template #header>
            <div class="dynamic-column-header"><span>{{ field.label }}</span><el-popconfirm v-if="!field.is_system"
                :title="`确认删除“${field.label}”字段吗？`" confirm-button-text="删除" cancel-button-text="取消"
                @confirm="removeField(field)"><template #reference><button aria-label="删除字段"><el-icon>
                      <Delete />
                    </el-icon></button></template></el-popconfirm>
            </div>
          </template>
          <template #default="scope">
            <el-input-number v-if="field.type === 'number'" v-model="scope.row[field.key]" class="data-cell-number"
              :min="0" :precision="0" :controls="false" @change="(value: number | undefined) => saveCell(scope.row.id, field.key, value ?? 0)" />
            <el-input v-else v-model="scope.row[field.key]" class="data-cell-text" maxlength="100" placeholder="请输入"
              @change="(value: string) => saveCell(scope.row.id, field.key, value)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="72" fixed="right" align="center"><template #default="scope"><el-popconfirm
              title="确认删除这个账号吗？" confirm-button-text="删除" cancel-button-text="取消"
              @confirm="removeRow(scope.row.id)"><template #reference><button class="delete-account"
                  :aria-label="`删除${scope.row.account}`"><el-icon>
                    <Delete />
                  </el-icon></button></template></el-popconfirm></template></el-table-column>
      </el-table>
      <div class="account-table-foot"><span>共 {{ rows.length }} 个账号 · {{ fields.length }}
          个字段</span><span>数据修改后即时更新</span>
      </div>
    </section>
  </div>
</template>
