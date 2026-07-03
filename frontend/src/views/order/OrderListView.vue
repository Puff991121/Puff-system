<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Delete, Download, Edit, Plus, Refresh, Search, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  createOrder,
  deleteOrder,
  exportOrderFile,
  getOrders,
  importOrderFile,
  updateOrder,
  type Order,
  type PaymentMethod,
  type WorkFormat,
} from '@/api/orders'

const orders = ref<Order[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const keyword = ref('')
const payment = ref<PaymentMethod | ''>('')
const dateRange = ref<[Date, Date] | null>(null)
const dialogVisible = ref(false)
const submitting = ref(false)
const importing = ref(false)
const exporting = ref(false)
const editingId = ref<number | null>(null)
const importInputRef = ref<HTMLInputElement>()
const orderFormRef = ref<FormInstance>()
const orderForm = reactive({
  orderDate: '',
  requirement: '',
  template: '',
  format: '' as WorkFormat | '',
  school: '',
  price: undefined as number | undefined,
  payment: '' as PaymentMethod | '',
})

const formRules: FormRules = {
  orderDate: [{ required: true, message: '请选择订单日期', trigger: 'change' }],
  requirement: [{ required: true, message: '请输入作业要求', trigger: 'blur' }],
  template: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  format: [{ required: true, message: '请选择格式', trigger: 'change' }],
  school: [{ required: true, message: '请输入学校名称', trigger: 'blur' }],
  price: [{ required: true, message: '请输入订单价格', trigger: 'blur' }],
  payment: [{ required: true, message: '请选择支付方式', trigger: 'change' }],
}

const formatDate = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const filterParams = () => ({
  keyword: keyword.value.trim() || undefined,
  payment_method: payment.value || undefined,
  start_date: dateRange.value ? formatDate(dateRange.value[0]) : undefined,
  end_date: dateRange.value ? formatDate(dateRange.value[1]) : undefined,
  sort_by: 'order_date' as const,
  sort_order: 'desc' as const,
})

const loadOrders = async () => {
  loading.value = true
  try {
    const result = await getOrders({
      page: page.value,
      page_size: pageSize.value,
      ...filterParams(),
    })
    orders.value = result.data.items
    total.value = result.data.total
  } finally {
    loading.value = false
  }
}

let filterTimer: ReturnType<typeof setTimeout> | undefined
watch([keyword, payment, dateRange], () => {
  page.value = 1
  clearTimeout(filterTimer)
  filterTimer = setTimeout(loadOrders, 300)
})

onMounted(loadOrders)
onBeforeUnmount(() => clearTimeout(filterTimer))

const resetFilters = () => {
  keyword.value = ''
  payment.value = ''
  dateRange.value = null
}

const exportOrders = async () => {
  exporting.value = true
  try {
    const blob = await exportOrderFile(filterParams())
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `orders-${formatDate(new Date()).replace(/-/g, '')}.xlsx`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
    ElMessage.success('订单导出成功')
  } finally {
    exporting.value = false
  }
}

const openImportPicker = () => importInputRef.value?.click()

const importOrders = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  importing.value = true
  try {
    const result = await importOrderFile(file)
    const { success_count, failed_count, errors } = result.data
    if (failed_count) {
      const firstError = errors[0]
      ElMessage.warning(
        `成功导入 ${success_count} 条，失败 ${failed_count} 条${firstError ? `；第 ${firstError.row} 行：${firstError.message}` : ''}`,
      )
    } else {
      ElMessage.success(`成功导入 ${success_count} 条订单`)
    }
    page.value = 1
    await loadOrders()
  } finally {
    importing.value = false
  }
}

const openCreateDialog = async () => {
  editingId.value = null
  Object.assign(orderForm, {
    orderDate: formatDate(new Date()),
    requirement: '',
    template: '',
    format: '',
    school: '',
    price: undefined,
    payment: '',
  })
  dialogVisible.value = true
  await nextTick()
  orderFormRef.value?.clearValidate()
}

const openEditDialog = async (order: Order) => {
  editingId.value = order.id
  Object.assign(orderForm, {
    orderDate: order.order_date,
    requirement: order.requirement,
    template: order.template,
    format: order.format,
    school: order.school,
    price: Number(order.price),
    payment: order.payment_method,
  })
  dialogVisible.value = true
  await nextTick()
  orderFormRef.value?.clearValidate()
}

const removeOrder = async (id: number) => {
  await deleteOrder(id)
  ElMessage.success('订单删除成功')
  if (orders.value.length === 1 && page.value > 1) page.value -= 1
  await loadOrders()
}

const submitOrder = async () => {
  if (!orderFormRef.value || !(await orderFormRef.value.validate())) return
  submitting.value = true
  const payload = {
    order_date: orderForm.orderDate,
    requirement: orderForm.requirement,
    template: orderForm.template,
    format: orderForm.format as WorkFormat,
    school: orderForm.school,
    price: Number(orderForm.price).toFixed(2),
    payment_method: orderForm.payment as PaymentMethod,
  }
  try {
    if (editingId.value !== null) {
      await updateOrder(editingId.value, payload)
      ElMessage.success('订单修改成功')
    } else {
      await createOrder(payload)
      ElMessage.success('订单新增成功')
    }
    dialogVisible.value = false
    page.value = 1
    await loadOrders()
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page-enter order-page">
    <div class="page-heading">
      <div><span class="kicker">ORDER CENTER</span>
        <h2>订单管理</h2>
        <p>集中查看作业需求、模板选用与支付信息。</p>
      </div>
      <div class="heading-actions"><input ref="importInputRef" class="visually-hidden" type="file" accept=".xlsx"
          @change="importOrders" /><el-button :icon="Upload" size="large" :loading="importing"
          @click="openImportPicker">导入订单</el-button><el-button :icon="Download" size="large" :loading="exporting"
          @click="exportOrders">导出订单</el-button><el-button type="primary" :icon="Plus" size="large"
          @click="openCreateDialog">新增订单</el-button></div>
    </div>

    <section class="order-summary">
      <div><span>今日订单</span><strong>18</strong><small>较昨日 +12.5%</small></div>
      <div><span>今日成交</span><strong>¥ 4,286</strong><small>已支付 15 笔</small></div>
      <div><span>待支付</span><strong>3</strong><small>金额 ¥ 867</small></div>
    </section>

    <section class="panel resource-panel order-panel">
      <div class="toolbar order-toolbar">
        <el-input v-model="keyword" :prefix-icon="Search" placeholder="搜索订单、要求、模板或学校" clearable />
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期"
          end-placeholder="结束日期" />
        <el-select v-model="payment" placeholder="全部支付方式" clearable>
          <el-option label="微信" value="微信" />
          <el-option label="咸鱼" value="咸鱼" />
          <el-option label="小红书" value="小红书" />
          <el-option label="支付宝" value="支付宝" />
        </el-select>
        <el-button :icon="Refresh" aria-label="重置筛选" @click="resetFilters">重置</el-button>
      </div>

      <el-table v-loading="loading" :data="orders" empty-text="暂无符合条件的订单">
        <el-table-column label="日期" width="118">
          <template #default="scope">
            <div class="order-time"><strong>{{ scope.row.order_date }}</strong></div>
          </template>
        </el-table-column>
        <el-table-column label="作业要求" min-width="200">
          <template #default="scope">
            <div class="requirement-cell"><strong>{{ scope.row.requirement }}</strong></div>
          </template>
        </el-table-column>
        <el-table-column prop="template" label="模板" min-width="150" />
        <el-table-column label="格式" min-width="95"><template #default="scope"><span class="format-badge">{{
          scope.row.format }}</span></template></el-table-column>
        <el-table-column prop="school" label="学校" min-width="130" />
        <el-table-column label="价格" min-width="105">
          <template #default="scope"><strong class="order-price">¥ {{ Number(scope.row.price).toFixed(2)
          }}</strong></template>
        </el-table-column>
        <el-table-column label="支付方式" min-width="115">
          <template #default="scope"><span class="payment-chip"
              :class="scope.row.payment_method === '微信' ? 'wechat' : scope.row.payment_method === '支付宝' ? 'alipay' : scope.row.payment_method === '小红书' ? 'redbook' : 'xianyu'">{{
                scope.row.payment_method }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right" align="center">
          <template #default="scope">
            <div class="order-row-actions"><button class="order-icon-action edit" title="修改订单" aria-label="修改订单"
                @click="openEditDialog(scope.row)"><el-icon>
                  <Edit />
                </el-icon></button><el-popconfirm title="确认删除这条订单吗？" confirm-button-text="删除" cancel-button-text="取消"
                @confirm="removeOrder(scope.row.id)"><template #reference><button class="order-icon-action remove"
                    title="删除订单" aria-label="删除订单"><el-icon>
                      <Delete />
                    </el-icon></button></template></el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination"><el-pagination v-model:current-page="page" v-model:page-size="pageSize"
          layout="total, prev, pager, next" :total="total" @current-change="loadOrders" /></div>
    </section>

    <el-dialog v-model="dialogVisible" class="order-dialog" modal-class="order-dialog-overlay" width="760px"
      align-center destroy-on-close :close-on-click-modal="false">
      <template #header>
        <div class="dialog-heading"><span>{{ editingId ? 'EDIT ORDER' : 'NEW ORDER' }}</span>
          <h3>{{ editingId ? '修改订单' : '新增订单' }}</h3>
        </div>
      </template>
      <el-form ref="orderFormRef" :model="orderForm" :rules="formRules" label-position="top">
        <el-form-item label="作业要求" prop="requirement"><el-input v-model="orderForm.requirement" type="textarea"
            :rows="2" maxlength="500" show-word-limit placeholder="请描述作业类型、字数、截止时间等具体要求" /></el-form-item>
        <div class="order-form-grid">
          <el-form-item label="日期" prop="orderDate"><el-date-picker v-model="orderForm.orderDate" type="date"
              value-format="YYYY-MM-DD" format="YYYY-MM-DD" placeholder="请选择订单日期" /></el-form-item>
          <el-form-item label="模板" prop="template"><el-input v-model="orderForm.template"
              placeholder="例如：定做还是模板" /></el-form-item>
          <el-form-item label="格式" prop="format"><el-select v-model="orderForm.format" placeholder="请选择格式"><el-option
                label="Figma" value="Figma" /><el-option label="Psd" value="Psd" /><el-option label="Xd"
                value="Xd" /><el-option label="Jsd" value="Jsd" /><el-option label="Html" value="Html" /><el-option
                label="定做" value="定做" /><el-option label="无" value="无" /></el-select></el-form-item>
          <el-form-item label="学校" prop="school"><el-input v-model="orderForm.school"
              placeholder="请输入学校名称" /></el-form-item>
          <el-form-item label="价格" prop="price"><el-input-number v-model="orderForm.price" :min="0.01" :precision="2"
              :step="10" controls-position="right" placeholder="0.00" /></el-form-item>
          <el-form-item label="支付方式" prop="payment"><el-select v-model="orderForm.payment"
              placeholder="请选择支付方式"><el-option label="微信" value="微信" /><el-option label="咸鱼" value="咸鱼" /><el-option
                label="小红书" value="小红书" /><el-option label="支付宝" value="支付宝" /></el-select></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary"
          :loading="submitting" @click="submitOrder">{{ editingId ? '保存修改' : '确认新增' }}</el-button></template>
    </el-dialog>
  </div>
</template>
