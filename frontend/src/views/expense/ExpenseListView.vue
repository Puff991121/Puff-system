<script setup lang="ts">
import { nextTick, onMounted, reactive, ref, watch } from 'vue'
import { Delete, Download, Edit, Plus, Refresh, Search, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { createExpense, deleteExpense, exportExpenseFile, getExpenses, getExpenseSummary, importExpenseFile, updateExpense, type Expense } from '@/api/expenses'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const rows = ref<Expense[]>([]), loading = ref(false), page = ref(1), total = ref(0)
const sortBy = ref<'transaction_time' | 'amount'>('transaction_time'), sortOrder = ref<'asc' | 'desc'>('desc')
const description = ref(''), transactionType = ref(''), payment = ref('')
const dateRange = ref<[Date, Date] | null>(null), dialogVisible = ref(false), editingId = ref<number | null>(null)
const submitting = ref(false), importing = ref(false), exporting = ref(false), inputRef = ref<HTMLInputElement>(), formRef = ref<FormInstance>()
const summary = reactive({ today_amount: '0.00', today_count: 0, month_amount: '0.00', month_count: 0, month_change_rate: null as string | null, year_amount: '0.00', year_count: 0, year_change_rate: null as string | null, total_amount: '0.00', total_count: 0 })
const form = reactive({ transactionTime: '', transactionType: '', counterparty: '', description: '', amount: undefined as number | undefined, payment: '' })
const rules: FormRules = { transactionTime: [{ required: true, message: '请选择交易时间' }], transactionType: [{ required: true, message: '请输入交易类型' }], counterparty: [{ required: true, message: '请输入交易对方' }], description: [{ required: true, message: '请输入商品说明' }], amount: [{ required: true, message: '请输入金额' }], payment: [{ required: true, message: '请输入支付方式' }] }
const pad = (n: number) => String(n).padStart(2, '0')
const localTime = (date = new Date()) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
const iso = (d: Date, end = false) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${end ? '23:59:59' : '00:00:00'}+08:00`
const dateText = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
const filters = () => ({ description: description.value.trim() || undefined, transaction_type: transactionType.value || undefined, payment_method: payment.value || undefined, start_time: dateRange.value ? iso(dateRange.value[0]) : undefined, end_time: dateRange.value ? iso(dateRange.value[1], true) : undefined })
const load = async () => { loading.value = true; try { const res = await getExpenses({ page: page.value, page_size: 10, sort_by: sortBy.value, sort_order: sortOrder.value, ...filters() }); rows.value = res.data.items; total.value = res.data.total } finally { loading.value = false } }
const loadSummary = async () => Object.assign(summary, (await getExpenseSummary(dateRange.value ? dateText(dateRange.value[0]) : undefined)).data)
const refresh = () => Promise.all([load(), loadSummary()])
let timer: ReturnType<typeof setTimeout>
watch([description, transactionType, payment, dateRange], (_, previous) => { page.value = 1; clearTimeout(timer); const dateChanged = previous?.[3] !== dateRange.value; timer = setTimeout(() => dateChanged ? refresh() : load(), 300) })
onMounted(refresh)
const reset = () => { description.value = ''; transactionType.value = ''; payment.value = ''; dateRange.value = null }
const changeAmountSort = ({ order }: { order: 'ascending' | 'descending' | null }) => { sortBy.value = order ? 'amount' : 'transaction_time'; sortOrder.value = order === 'ascending' ? 'asc' : 'desc'; page.value = 1; load() }
const openCreate = async () => { editingId.value = null; Object.assign(form, { transactionTime: localTime(), transactionType: '', counterparty: '', description: '', amount: undefined, payment: '' }); dialogVisible.value = true; await nextTick(); formRef.value?.clearValidate() }
const openEdit = async (row: Expense) => { editingId.value = row.id; Object.assign(form, { transactionTime: row.transaction_time.slice(0, 19).replace('T', ' '), transactionType: row.transaction_type, counterparty: row.counterparty, description: row.description, amount: Number(row.amount), payment: row.payment_method }); dialogVisible.value = true; await nextTick(); formRef.value?.clearValidate() }
const submit = async () => { if (!formRef.value || !(await formRef.value.validate())) return; submitting.value = true; try { const payload = { transaction_time: form.transactionTime.replace(' ', 'T') + '+08:00', transaction_type: form.transactionType.trim(), counterparty: form.counterparty, description: form.description, amount: Number(form.amount).toFixed(2), payment_method: form.payment.trim() }; editingId.value ? await updateExpense(editingId.value, payload) : await createExpense(payload); ElMessage.success(editingId.value ? '消费记录已修改' : '消费记录已新增'); dialogVisible.value = false; await refresh() } finally { submitting.value = false } }
const remove = async (id: number) => { await deleteExpense(id); ElMessage.success('消费记录已删除'); await refresh() }
const importFile = async (event: Event) => { const input = event.target as HTMLInputElement, file = input.files?.[0]; input.value = ''; if (!file) return; importing.value = true; try { const res = await importExpenseFile(file); ElMessage.success(`成功导入 ${res.data.success_count} 条，失败 ${res.data.failed_count} 条`); await refresh() } finally { importing.value = false } }
const exportFile = async () => { exporting.value = true; try { const blob = await exportExpenseFile(filters()); const url = URL.createObjectURL(blob), a = document.createElement('a'); a.href = url; a.download = `消费记录-${Date.now()}.xlsx`; a.click(); URL.revokeObjectURL(url); ElMessage.success('消费记录导出成功') } finally { exporting.value = false } }
const money = (value: string) => `¥ ${Number(value).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`
const trendText = (value: string | null, label: string) => value === null ? `${label}暂无可比数据` : `${label}${Number(value) >= 0 ? '上升' : '下降'} ${Math.abs(Number(value)).toFixed(2)}%`
const shortCounterparty = (value: string) => Array.from(value).slice(0, 6).join('')
const transactionTypeLabel = (value: string) => value === '微信红包（单发）' ? '微信红包' : value
const paymentLabel = (value: string) => {
  if (value === '平安银行信用卡(7735)') return '平安信用卡'
  if (value === '余额宝&支付宝随机抽立减' || value === '花呗&到店支付立减券') return '支付宝'
  if (value === '零钱' || value === '零钱通') return '微信'
  return value
}
</script>

<template>
  <div class="page-enter expense-page">
    <div class="page-heading">
      <div><span class="kicker">SPENDING LEDGER</span>
        <h2>消费记录</h2>
        <p>把每一笔支出去向，变成清楚、可追溯的账目。</p>
      </div>
      <div class="heading-actions"><input ref="inputRef" class="visually-hidden" type="file" accept=".xlsx"
          @change="importFile"><el-button :icon="Upload" size="large" :loading="importing"
          @click="inputRef?.click()">导入记录</el-button><el-button :icon="Download" size="large" :loading="exporting"
          @click="exportFile">导出记录</el-button><el-button type="primary" :icon="Plus" size="large"
          @click="openCreate">新增消费</el-button></div>
    </div>
    <section class="expense-summary">
      <div><span>今日消费</span><strong>{{ money(summary.today_amount) }}</strong><small>{{ summary.today_count }}
          笔消费</small></div>
      <div><span>{{ dateRange ? `${dateRange[0].getMonth() + 1}月消费` : '本月消费' }}</span><strong>{{
        money(summary.month_amount) }}</strong><small class="trend"
          :class="{ down: Number(summary.month_change_rate) < 0 }">{{ trendText(summary.month_change_rate, '环比')
          }}</small></div>
      <div><span>本年消费</span><strong>{{ money(summary.year_amount) }}</strong><small class="trend"
          :class="{ down: Number(summary.year_change_rate) < 0 }">{{ trendText(summary.year_change_rate, '同比')
          }}</small></div>
      <div><span>累计消费</span><strong>{{ money(summary.total_amount) }}</strong><small>共 {{ summary.total_count }}
          笔记录</small></div>
    </section>
    <section class="panel expense-panel">
      <div class="expense-toolbar"><el-input v-model="description" :prefix-icon="Search" placeholder="搜索商品说明"
          clearable /><el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始时间"
          end-placeholder="结束时间" /><el-input v-model="transactionType" placeholder="输入交易类型" maxlength="30"
          clearable /><el-input v-model="payment" placeholder="输入支付方式" maxlength="30" clearable /><el-button
          :icon="Refresh" @click="reset">重置</el-button></div>
      <el-table v-loading="loading" :data="rows" empty-text="暂无符合条件的消费记录" @sort-change="changeAmountSort">
        <el-table-column label="交易时间" width="178"><template #default="s"><strong class="time-cell">{{
          s.row.transaction_time.slice(0, 19).replace('T', ' ') }}</strong></template></el-table-column>
        <el-table-column label="交易类型" width="140"><template #default="s"><span class="type-chip">{{
          transactionTypeLabel(s.row.transaction_type) }}</span></template></el-table-column>
        <el-table-column label="交易对方" min-width="100"><template #default="s">{{ shortCounterparty(s.row.counterparty)
            }}</template></el-table-column>
        <el-table-column prop="description" label="商品说明" min-width="120" show-overflow-tooltip />
        <el-table-column prop="amount" label="金额" width="130" sortable="custom"><template #default="s"><strong
              class="amount-cell">- {{ money(s.row.amount) }}</strong></template></el-table-column>
        <el-table-column label="支付方式" width="200"><template #default="s"><span class="payment-chip">{{
          paymentLabel(s.row.payment_method) }}</span></template></el-table-column>
        <el-table-column label="操作" width="92" fixed="right" align="center"><template #default="s">
            <div class="row-actions"><button aria-label="修改" @click="openEdit(s.row)"><el-icon>
                  <Edit />
                </el-icon></button><el-popconfirm title="确认删除这条记录吗？" @confirm="remove(s.row.id)"><template
                  #reference><button class="delete" aria-label="删除"><el-icon>
                      <Delete />
                    </el-icon></button></template></el-popconfirm>
            </div>
          </template></el-table-column>
      </el-table>
      <div class="pagination"><el-pagination v-model:current-page="page" layout="total, prev, pager, next"
          :total="total" @current-change="load" /></div>
    </section>
    <el-dialog v-model="dialogVisible" class="order-dialog"
      :modal-class="`order-dialog-overlay ${appStore.sidebarCollapsed ? 'is-sidebar-collapsed' : ''}`" width="640px"
      align-center append-to-body destroy-on-close :close-on-click-modal="false"><template #header>
        <div class="dialog-heading"><span>{{ editingId ? 'EDIT EXPENSE' : 'NEW EXPENSE' }}</span>
          <h3>{{ editingId ? '修改消费记录' : '新增消费记录' }}</h3>
        </div>
      </template><el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <div class="form-grid"><el-form-item label="交易时间" prop="transactionTime"><el-date-picker
              v-model="form.transactionTime" type="datetime" value-format="YYYY-MM-DD HH:mm:ss"
              placeholder="请选择交易时间" /></el-form-item><el-form-item label="交易类型" prop="transactionType"><el-input
              v-model="form.transactionType" maxlength="30" placeholder="例如：交通出行" /></el-form-item><el-form-item
            label="交易对方" prop="counterparty"><el-input v-model="form.counterparty" maxlength="100"
              placeholder="商户或个人名称" /></el-form-item><el-form-item label="支付方式" prop="payment"><el-input
              v-model="form.payment" maxlength="30" placeholder="例如：余额宝或信用卡" /></el-form-item><el-form-item label="金额"
            prop="amount"><el-input-number v-model="form.amount" :min="0.01" :precision="2"
              controls-position="right" /></el-form-item><el-form-item class="wide" label="商品说明"
            prop="description"><el-input v-model="form.description" type="textarea" :rows="3" maxlength="300"
              show-word-limit placeholder="记录购买的商品或服务" /></el-form-item></div>
      </el-form><template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary"
          :loading="submitting" @click="submit">保存记录</el-button></template></el-dialog>
  </div>
</template>

<style scoped>
.expense-page {
  display: flex;
  flex-direction: column;
  gap: 22px
}

.page-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between
}

.kicker {
  color: #169a6c;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 2px
}

.page-heading h2 {
  margin: 5px 0 4px;
  font-size: 30px;
  letter-spacing: -1px
}

.page-heading p {
  color: var(--muted)
}

.heading-actions {
  display: flex;
  gap: 10px
}

.expense-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid var(--line);
  border-radius: 18px;
  overflow: hidden;
  background: var(--surface);
  box-shadow: var(--shadow)
}

.expense-summary>div {
  display: flex;
  min-height: 126px;
  padding: 24px 28px;
  flex-direction: column;
  justify-content: center;
  border-right: 1px solid var(--line)
}

.expense-summary>div:last-child {
  border: 0
}

.expense-summary span {
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 1px
}

.expense-summary strong {
  margin: 8px 0 2px;
  font-size: 25px
}

.expense-summary small {
  color: #89928e
}

.expense-summary .trend {
  color: #d45b4d
}

.expense-summary .trend.down {
  color: #169a6c
}

.panel {
  border: 1px solid var(--line);
  border-radius: 18px;
  background: var(--surface);
  box-shadow: var(--shadow);
  overflow: hidden
}

.expense-toolbar {
  display: grid;
  grid-template-columns: 1.3fr 1.5fr .85fr .85fr auto;
  gap: 10px;
  padding: 18px;
  border-bottom: 1px solid var(--line)
}

.time-cell {
  font-size: 13px
}

.amount-cell {
  color: #d65b4a
}

.type-chip,
.payment-chip {
  display: inline-flex;
  padding: 5px 9px;
  border-radius: 999px;
  font-size: 12px;
  background: #eef5e7;
  color: #45623d
}

.payment-chip {
  background: #edf3f2;
  color: #49605a
}

.row-actions {
  display: flex;
  justify-content: center;
  gap: 5px
}

.row-actions button {
  display: grid;
  width: 30px;
  height: 30px;
  padding: 0;
  place-items: center;
  border: 0;
  border-radius: 8px;
  color: #2b7560;
  background: #edf7f2
}

.row-actions button.delete {
  color: #bd5549;
  background: #fff0ed
}

.pagination {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 18px
}

.form-grid .wide {
  grid-column: 1/-1
}

.form-grid :deep(.el-date-editor),
.form-grid :deep(.el-select),
.form-grid :deep(.el-input-number) {
  width: 100%
}

@media(max-width:1100px) {
  .expense-toolbar {
    grid-template-columns: 1fr 1fr
  }

  .expense-summary {
    grid-template-columns: 1fr 1fr
  }

  .page-heading {
    align-items: flex-start;
    gap: 18px;
    flex-direction: column
  }
}

@media(max-width:700px) {
  .heading-actions {
    flex-wrap: wrap
  }

  .expense-summary {
    grid-template-columns: 1fr
  }

  .expense-summary>div {
    border-right: 0;
    border-bottom: 1px solid var(--line)
  }

  .expense-toolbar,
  .form-grid {
    grid-template-columns: 1fr
  }

  .form-grid .wide {
    grid-column: auto
  }
}
</style>
