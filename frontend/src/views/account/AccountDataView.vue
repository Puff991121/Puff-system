<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { Check, Delete, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

type FieldType = 'text' | 'number'
interface TableField { key: string; label: string; type: FieldType; custom?: boolean }
interface AccountRow { id: number;[key: string]: string | number }

const fields = reactive<TableField[]>([
  { key: 'account', label: '账号', type: 'text' },
  { key: 'followers', label: '粉丝', type: 'number' },
  { key: 'notes', label: '发布笔记数', type: 'number' },
])

const rows = reactive<AccountRow[]>([
  { id: 1, account: 'DW网页设计', followers: 1629, notes: 3 },
  { id: 2, account: '了不起的啊点', followers: 329, notes: 7 },
  { id: 3, account: '阿秋', followers: 79, notes: 2 },
  { id: 4, account: '爱吃泡芙', followers: 15, notes: 3 },
])

const fieldPopoverVisible = ref(false)
const newField = reactive<{ label: string; type: FieldType }>({ label: '', type: 'text' })
const lastUpdated = ref('刚刚')
const totalFollowers = computed(() => rows.reduce((sum, row) => sum + Number(row.followers || 0), 0))
const totalNotes = computed(() => rows.reduce((sum, row) => sum + Number(row.notes || 0), 0))

const markUpdated = () => {
  lastUpdated.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const addField = () => {
  const label = newField.label.trim()
  if (!label) return ElMessage.warning('请输入字段名称')
  if (fields.some((field) => field.label === label)) return ElMessage.warning('该字段已存在')
  const key = `custom_${Date.now()}`
  fields.push({ key, label, type: newField.type, custom: true })
  rows.forEach((row) => { row[key] = newField.type === 'number' ? 0 : '' })
  newField.label = ''
  newField.type = 'text'
  fieldPopoverVisible.value = false
  markUpdated()
  ElMessage.success(`字段“${label}”已添加`)
}

const removeField = (field: TableField) => {
  const index = fields.findIndex((item) => item.key === field.key)
  if (index !== -1) fields.splice(index, 1)
  rows.forEach((row) => { delete row[field.key] })
  markUpdated()
}

const addRow = () => {
  const row: AccountRow = { id: Math.max(0, ...rows.map((item) => item.id)) + 1 }
  fields.forEach((field) => { row[field.key] = field.type === 'number' ? 0 : '' })
  row.account = '新账号'
  rows.push(row)
  markUpdated()
}

const removeRow = (id: number) => {
  const index = rows.findIndex((row) => row.id === id)
  if (index !== -1) rows.splice(index, 1)
  markUpdated()
}
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
      <div><span>账号数量</span><strong>{{ rows.length }}</strong><small>ACCOUNTS</small></div>
      <div><span>粉丝总数</span><strong>{{ totalFollowers.toLocaleString('zh-CN') }}</strong><small>FOLLOWERS</small></div>
      <div><span>发布笔记</span><strong>{{ totalNotes }}</strong><small>NOTES</small></div>
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

      <el-table :data="rows" row-key="id" empty-text="暂无账号数据">
        <el-table-column v-for="field in fields" :key="field.key" :min-width="field.key === 'account' ? 210 : 150">
          <template #header>
            <div class="dynamic-column-header"><span>{{ field.label }}</span><el-popconfirm v-if="field.custom"
                :title="`确认删除“${field.label}”字段吗？`" confirm-button-text="删除" cancel-button-text="取消"
                @confirm="removeField(field)"><template #reference><button aria-label="删除字段"><el-icon>
                      <Delete />
                    </el-icon></button></template></el-popconfirm>
            </div>
          </template>
          <template #default="scope">
            <el-input-number v-if="field.type === 'number'" v-model="scope.row[field.key]" class="data-cell-number"
              :min="0" :precision="0" :controls="false" @change="markUpdated" />
            <el-input v-else v-model="scope.row[field.key]" class="data-cell-text" maxlength="100" placeholder="请输入"
              @change="markUpdated" />
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
