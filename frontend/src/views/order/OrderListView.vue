<script setup lang="ts">
import { computed, nextTick, reactive, ref } from 'vue'
import { Delete, Download, Edit, Plus, Refresh, Search, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import readXlsxFile from 'read-excel-file/browser'

type PaymentMethod = '微信' | '咸鱼' | '小红书' | '支付宝'
type WorkFormat = 'Figma' | 'Psd' | 'Xd' | 'Jsd' | 'Html' | '定做' | '无'
const paymentMethods: PaymentMethod[] = ['微信', '咸鱼', '小红书', '支付宝']
const workFormats: WorkFormat[] = ['Figma', 'Psd', 'Xd', 'Jsd', 'Html', '定做', '无']
const excelHeaders = ['日期', '作业要求', '模板', '格式', '学校', '价格', '支付方式']

interface Order {
  id: string
  createdAt: string
  requirement: string
  template: string
  format: WorkFormat
  school: string
  price: number
  payment: PaymentMethod
}

const keyword = ref('')
const payment = ref('')
const dateRange = ref<[Date, Date] | null>(null)
const dialogVisible = ref(false)
const submitting = ref(false)
const editingId = ref<string | null>(null)
const importInputRef = ref<HTMLInputElement>()
const orderFormRef = ref<FormInstance>()
const orderForm = reactive({ requirement: '', template: '', format: '' as WorkFormat | '', school: '', price: undefined as number | undefined, payment: '' as PaymentMethod | '' })

const formRules: FormRules = {
  requirement: [{ required: true, message: '请输入作业要求', trigger: 'blur' }],
  template: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  format: [{ required: true, message: '请选择格式', trigger: 'change' }],
  school: [{ required: true, message: '请输入学校名称', trigger: 'blur' }],
  price: [{ required: true, message: '请输入订单价格', trigger: 'blur' }],
  payment: [{ required: true, message: '请选择支付方式', trigger: 'change' }],
}

const orders = ref<Order[]>([
  { id: 'PF-20260702-018', createdAt: '2026-07-02 10:42', requirement: '市场营销课程论文，3000 字，需附数据分析', template: '学术论文标准版', format: '无', school: '复旦大学', price: 299, payment: '微信' },
  { id: 'PF-20260702-017', createdAt: '2026-07-02 09:18', requirement: '计算机网络实验报告，包含拓扑图与结果说明', template: '实验报告模板', format: 'Html', school: '上海交通大学', price: 168, payment: '支付宝' },
  { id: 'PF-20260701-016', createdAt: '2026-07-01 22:06', requirement: '毕业设计开题报告，研究方向为智能推荐系统', template: '本科开题报告', format: 'Figma', school: '浙江大学', price: 399, payment: '小红书' },
  { id: 'PF-20260701-015', createdAt: '2026-07-01 17:35', requirement: '品牌策划方案，需包含用户画像和传播路径', template: '商业策划书', format: 'Psd', school: '同济大学', price: 258, payment: '微信' },
  { id: 'PF-20260701-014', createdAt: '2026-07-01 14:20', requirement: '宏观经济学案例分析，使用近五年公开数据', template: '课程论文精简版', format: '定做', school: '南京大学', price: 219, payment: '支付宝' },
])

const filteredOrders = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return orders.value.filter((order) => {
    const matchesKeyword = !query || [order.id, order.requirement, order.template, order.format, order.school].some((value) => value.toLowerCase().includes(query))
    const matchesPayment = !payment.value || order.payment === payment.value
    const orderDate = new Date(order.createdAt.replace(' ', 'T'))
    const rangeEnd = dateRange.value ? new Date(dateRange.value[1]) : null
    rangeEnd?.setHours(23, 59, 59, 999)
    const matchesDate = !dateRange.value || (orderDate >= dateRange.value[0] && orderDate <= rangeEnd!)
    return matchesKeyword && matchesPayment && matchesDate
  })
})

const resetFilters = () => {
  keyword.value = ''
  payment.value = ''
  dateRange.value = null
}

const exportOrders = () => ElMessage.success('订单导出任务已创建')

const openImportPicker = () => importInputRef.value?.click()

const parseExcelDate = (value: unknown) => {
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    const pad = (part: number) => String(part).padStart(2, '0')
    return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}`
  }
  const text = String(value ?? '').trim().replace(/[/.]/g, '-')
  const match = text.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/)
  return match ? `${match[1]}-${match[2].padStart(2, '0')}-${match[3].padStart(2, '0')}` : ''
}

const importOrders = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (file.size > 5 * 1024 * 1024) return ElMessage.error('Excel 文件不能超过 5MB')

  try {
    const workbookSheets = await readXlsxFile(file)
    const sheetRows = workbookSheets[0]?.data
    if (!sheetRows?.length) return ElMessage.error('Excel 中没有可读取的数据')
    const actualHeaders = sheetRows[0].map((item) => String(item ?? '').trim())
    const missingHeaders = excelHeaders.filter((header) => !actualHeaders.includes(header))
    if (missingHeaders.length) return ElMessage.error(`缺少表头：${missingHeaders.join('、')}`)
    const rows = sheetRows.slice(1).filter((row) => row.some((cell) => cell !== null && String(cell).trim() !== '')).map((row) =>
      Object.fromEntries(actualHeaders.map((header, index) => [header, row[index] ?? ''])),
    )
    if (!rows.length) return ElMessage.warning('Excel 中没有订单数据')

    const imported: Order[] = []
    let invalidCount = 0
    rows.forEach((row, index) => {
      const date = parseExcelDate(row['日期'])
      const requirement = String(row['作业要求'] ?? '').trim()
      const template = String(row['模板'] ?? '').trim()
      const format = String(row['格式'] ?? '').trim() as WorkFormat
      const school = String(row['学校'] ?? '').trim()
      const price = Number(row['价格'])
      const paymentMethod = String(row['支付方式'] ?? '').trim() as PaymentMethod
      if (!date || !requirement || !template || !school || !Number.isFinite(price) || price < 0 || !workFormats.includes(format) || !paymentMethods.includes(paymentMethod)) {
        invalidCount += 1
        return
      }
      imported.push({
        id: `IMP-${date.replace(/-/g, '')}-${String(Date.now() + index).slice(-8)}`,
        createdAt: `${date} 00:00`,
        requirement,
        template,
        format,
        school,
        price,
        payment: paymentMethod,
      })
    })

    if (!imported.length) return ElMessage.error('没有符合要求的订单，请检查数据格式')
    orders.value.unshift(...imported)
    ElMessage.success(`成功导入 ${imported.length} 条订单${invalidCount ? `，跳过 ${invalidCount} 条无效数据` : ''}`)
  } catch {
    ElMessage.error('Excel 解析失败，请确认文件格式正确')
  }
}

const openCreateDialog = async () => {
  editingId.value = null
  Object.assign(orderForm, { requirement: '', template: '', format: '', school: '', price: undefined, payment: '' })
  dialogVisible.value = true
  await nextTick()
  orderFormRef.value?.clearValidate()
}

const openEditDialog = async (order: Order) => {
  editingId.value = order.id
  Object.assign(orderForm, {
    requirement: order.requirement,
    template: order.template,
    format: order.format,
    school: order.school,
    price: order.price,
    payment: order.payment,
  })
  dialogVisible.value = true
  await nextTick()
  orderFormRef.value?.clearValidate()
}

const removeOrder = (id: string) => {
  const index = orders.value.findIndex((order) => order.id === id)
  if (index !== -1) orders.value.splice(index, 1)
  ElMessage.success('订单删除成功')
}

const formatNow = () => {
  const now = new Date()
  const pad = (value: number) => String(value).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`
}

const submitOrder = async () => {
  if (!orderFormRef.value || !(await orderFormRef.value.validate())) return
  submitting.value = true
  await new Promise((resolve) => setTimeout(resolve, 350))
  if (editingId.value) {
    const order = orders.value.find((item) => item.id === editingId.value)
    if (order) Object.assign(order, {
      requirement: orderForm.requirement,
      template: orderForm.template,
      format: orderForm.format as WorkFormat,
      school: orderForm.school,
      price: orderForm.price!,
      payment: orderForm.payment as PaymentMethod,
    })
  } else {
    const sequence = String(orders.value.length + 19).padStart(3, '0')
    orders.value.unshift({
      id: `PF-${formatNow().slice(0, 10).replace(/-/g, '')}-${sequence}`,
      createdAt: formatNow(),
      requirement: orderForm.requirement,
      template: orderForm.template,
      format: orderForm.format as WorkFormat,
      school: orderForm.school,
      price: orderForm.price!,
      payment: orderForm.payment as PaymentMethod,
    })
  }
  submitting.value = false
  dialogVisible.value = false
  ElMessage.success(editingId.value ? '订单修改成功' : '订单新增成功')
}
</script>

<template>
  <div class="page-enter order-page">
    <div class="page-heading">
      <div><span class="kicker">ORDER CENTER</span><h2>订单管理</h2><p>集中查看作业需求、模板选用与支付信息。</p></div>
      <div class="heading-actions"><input ref="importInputRef" class="visually-hidden" type="file" accept=".xlsx" @change="importOrders" /><el-button :icon="Upload" size="large" @click="openImportPicker">导入订单</el-button><el-button :icon="Download" size="large" @click="exportOrders">导出订单</el-button><el-button type="primary" :icon="Plus" size="large" @click="openCreateDialog">新增订单</el-button></div>
    </div>

    <section class="order-summary">
      <div><span>今日订单</span><strong>18</strong><small>较昨日 +12.5%</small></div>
      <div><span>今日成交</span><strong>¥ 4,286</strong><small>已支付 15 笔</small></div>
      <div><span>待支付</span><strong>3</strong><small>金额 ¥ 867</small></div>
    </section>

    <section class="panel resource-panel order-panel">
      <div class="toolbar order-toolbar">
        <el-input v-model="keyword" :prefix-icon="Search" placeholder="搜索订单、要求、模板或学校" clearable />
        <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" />
        <el-select v-model="payment" placeholder="全部支付方式" clearable>
          <el-option label="微信" value="微信" />
          <el-option label="咸鱼" value="咸鱼" />
          <el-option label="小红书" value="小红书" />
          <el-option label="支付宝" value="支付宝" />
        </el-select>
        <el-button :icon="Refresh" aria-label="重置筛选" @click="resetFilters">重置</el-button>
      </div>

      <el-table :data="filteredOrders" empty-text="暂无符合条件的订单">
        <el-table-column label="日期" width="118">
          <template #default="scope"><div class="order-time"><strong>{{ scope.row.createdAt.slice(0, 10) }}</strong></div></template>
        </el-table-column>
        <el-table-column label="作业要求" min-width="300">
          <template #default="scope"><div class="requirement-cell"><strong>{{ scope.row.requirement }}</strong></div></template>
        </el-table-column>
        <el-table-column prop="template" label="模板" min-width="150" />
        <el-table-column label="格式" min-width="95"><template #default="scope"><span class="format-badge">{{ scope.row.format }}</span></template></el-table-column>
        <el-table-column prop="school" label="学校" min-width="130" />
        <el-table-column label="价格" min-width="105">
          <template #default="scope"><strong class="order-price">¥ {{ scope.row.price.toFixed(2) }}</strong></template>
        </el-table-column>
        <el-table-column label="支付方式" min-width="115">
          <template #default="scope"><span class="payment-chip" :class="scope.row.payment === '微信' ? 'wechat' : scope.row.payment === '支付宝' ? 'alipay' : scope.row.payment === '小红书' ? 'redbook' : 'xianyu'">{{ scope.row.payment }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right" align="center">
          <template #default="scope"><div class="order-row-actions"><button class="order-icon-action edit" title="修改订单" aria-label="修改订单" @click="openEditDialog(scope.row)"><el-icon><Edit /></el-icon></button><el-popconfirm title="确认删除这条订单吗？" confirm-button-text="删除" cancel-button-text="取消" @confirm="removeOrder(scope.row.id)"><template #reference><button class="order-icon-action remove" title="删除订单" aria-label="删除订单"><el-icon><Delete /></el-icon></button></template></el-popconfirm></div></template>
        </el-table-column>
      </el-table>

      <div class="pagination"><span>共 {{ filteredOrders.length }} 条记录</span><el-pagination layout="prev, pager, next" :total="filteredOrders.length" :page-size="10" /></div>
    </section>

    <el-dialog
      v-model="dialogVisible"
      class="order-dialog"
      width="560px"
      align-center
      destroy-on-close
      :modal="false"
      :modal-penetrable="true"
      :lock-scroll="false"
    >
      <template #header><div class="dialog-heading"><span>{{ editingId ? 'EDIT ORDER' : 'NEW ORDER' }}</span><h3>{{ editingId ? '修改订单' : '新增订单' }}</h3><p>{{ editingId ? '更新当前订单的作业信息与收款渠道。' : '填写作业信息与收款渠道，创建后将出现在订单列表顶部。' }}</p></div></template>
      <el-form ref="orderFormRef" :model="orderForm" :rules="formRules" label-position="top">
        <el-form-item label="作业要求" prop="requirement"><el-input v-model="orderForm.requirement" type="textarea" :rows="4" maxlength="500" show-word-limit placeholder="请描述作业类型、字数、截止时间等具体要求" /></el-form-item>
        <div class="order-form-grid">
          <el-form-item label="模板" prop="template"><el-input v-model="orderForm.template" placeholder="例如：本科开题报告" /></el-form-item>
          <el-form-item label="格式" prop="format"><el-select v-model="orderForm.format" placeholder="请选择格式"><el-option label="Figma" value="Figma" /><el-option label="Psd" value="Psd" /><el-option label="Xd" value="Xd" /><el-option label="Jsd" value="Jsd" /><el-option label="Html" value="Html" /><el-option label="定做" value="定做" /><el-option label="无" value="无" /></el-select></el-form-item>
          <el-form-item label="学校" prop="school"><el-input v-model="orderForm.school" placeholder="请输入学校名称" /></el-form-item>
          <el-form-item label="价格" prop="price"><el-input-number v-model="orderForm.price" :min="0.01" :precision="2" :step="10" controls-position="right" placeholder="0.00" /></el-form-item>
          <el-form-item label="支付方式" prop="payment"><el-select v-model="orderForm.payment" placeholder="请选择支付方式"><el-option label="微信" value="微信" /><el-option label="咸鱼" value="咸鱼" /><el-option label="小红书" value="小红书" /><el-option label="支付宝" value="支付宝" /></el-select></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="submitting" @click="submitOrder">{{ editingId ? '保存修改' : '确认新增' }}</el-button></template>
    </el-dialog>
  </div>
</template>
