<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Calendar, Check, Delete, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  createAssetAccount,
  deleteAssetAccount,
  getAssetPage,
  updateAssetAccount,
  type AssetAccountType,
  type AssetSummary,
} from '@/api/assets'

interface AccountItem {
  id: number
  type: AssetAccountType
  account: string
  amount: number
  sortOrder: number
}

const loading = ref(false)
const assets = ref<AccountItem[]>([])
const liabilities = ref<AccountItem[]>([])
const repaymentDates = [
  { name: '平安', date: '每月7日' },
  { name: '招商', date: '每月9日' },
  { name: '美团', date: '每月15日' },
  { name: '白条', date: '每月20日' },
  { name: '花呗', date: '每月25日' },
]
const summary = ref<AssetSummary>({
  total_assets: '0.00',
  total_liabilities: '0.00',
  net_assets: '0.00',
  liability_ratio: '0.00',
  asset_account_count: 0,
  liability_account_count: 0,
  updated_at: '',
})

const totalAssets = computed(() => Number(summary.value.total_assets))
const totalLiabilities = computed(() => Number(summary.value.total_liabilities))
const netAssets = computed(() => Number(summary.value.net_assets))
const liabilityRatio = computed(() => Number(summary.value.liability_ratio))
const lastUpdated = computed(() => summary.value.updated_at
  ? new Date(summary.value.updated_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  : '--:--')

const formatMoney = (value: number) => new Intl.NumberFormat('zh-CN', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format(value)

const toViewItem = (item: {
  id: number
  type: AssetAccountType
  account: string
  amount: string
  sort_order: number
}): AccountItem => ({
  id: item.id,
  type: item.type,
  account: item.account,
  amount: Number(item.amount),
  sortOrder: item.sort_order,
})

const loadAssets = async () => {
  loading.value = true
  try {
    const result = await getAssetPage()
    summary.value = result.data.summary
    assets.value = result.data.assets.map(toViewItem)
    liabilities.value = result.data.liabilities.map(toViewItem)
  } finally {
    loading.value = false
  }
}

const addAccount = async (type: AssetAccountType) => {
  const target = type === 'asset' ? assets.value : liabilities.value
  const baseName = type === 'asset' ? '新资产账户' : '新负债账户'
  const existingNames = new Set(target.map((item) => item.account))
  let account = baseName
  let sequence = 2
  while (existingNames.has(account)) account = `${baseName} ${sequence++}`

  const result = await createAssetAccount({ type, account, amount: '0.00' })
  target.push(toViewItem(result.data.account))
  summary.value = result.data.summary
  ElMessage.success('账户新增成功，请修改账户名称和金额')
}

const saveAccount = async (item: AccountItem) => {
  try {
    const result = await updateAssetAccount(item.id, {
      account: item.account,
      amount: Number(item.amount).toFixed(2),
    })
    summary.value = result.data.summary
    Object.assign(item, toViewItem(result.data.account))
  } catch {
    await loadAssets()
  }
}

const removeAccount = async (type: AssetAccountType, id: number) => {
  const result = await deleteAssetAccount(id)
  const target = type === 'asset' ? assets.value : liabilities.value
  const index = target.findIndex((item) => item.id === id)
  if (index !== -1) target.splice(index, 1)
  summary.value = result.data.summary
  ElMessage.success('账户删除成功')
}

onMounted(loadAssets)
</script>

<template>
  <div class="page-enter asset-page">
    <div class="page-heading">
      <div><span class="kicker">FINANCIAL POSITION</span>
        <h2>资产管理</h2>
        <p>维护各账户余额，掌握当前财务状况。</p>
      </div>
      <div class="asset-sync"><el-icon>
          <Check />
        </el-icon><span>数据已同步 · {{ lastUpdated }}</span></div>
    </div>

    <aside class="repayment-reminder" aria-label="还款日期提醒">
      <div class="repayment-reminder-title">
        <span class="repayment-reminder-icon"><el-icon><Calendar /></el-icon></span>
        <div><strong>还款日提醒</strong><small>REPAYMENT DATES</small></div>
      </div>
      <ul class="repayment-date-list">
        <li v-for="item in repaymentDates" :key="item.name">
          <span>{{ item.name }}</span><strong>{{ item.date }}</strong>
        </li>
      </ul>
    </aside>

    <section v-loading="loading" class="asset-overview">
      <article class="asset-stat total">
        <div class="asset-stat-heading"><span>总资产</span><small>ASSETS</small></div>
        <strong><i>¥</i>{{ formatMoney(totalAssets) }}</strong>
        <div class="asset-stat-foot"><span>共 {{ summary.asset_account_count }} 个资产账户</span><i></i></div>
      </article>
      <article class="asset-stat liability">
        <div class="asset-stat-heading"><span>总负债</span><small>LIABILITIES</small></div>
        <strong><i>¥</i>-{{ formatMoney(Math.abs(totalLiabilities)) }}</strong>
        <div class="asset-stat-foot"><span>负债率 {{ liabilityRatio.toFixed(1) }}%</span><i></i></div>
      </article>
      <article class="asset-stat net">
        <div class="asset-stat-heading"><span>净资产</span><small>NET WORTH</small></div>
        <strong><i>¥</i>{{ formatMoney(netAssets) }}</strong>
        <div class="asset-stat-foot"><span>总资产 + 总负债</span><i></i></div>
      </article>
    </section>

    <div class="asset-ledgers">
      <section class="panel ledger-panel">
        <div class="ledger-heading">
          <div><span class="ledger-index">01</span>
            <div>
              <h3>资产账户</h3>
              <p>现金、银行存款及待结算款项</p>
            </div>
          </div>
          <div class="ledger-actions"><span class="ledger-total">¥ {{ formatMoney(totalAssets) }}</span><el-button
              :icon="Plus" size="small" @click="addAccount('asset')">新增账户</el-button></div>
        </div>
        <el-table v-loading="loading" :data="assets">
          <el-table-column label="账户" min-width="180"><template #default="scope">
              <div class="account-name"><el-input v-model="scope.row.account" class="account-editor" maxlength="30"
                  @change="saveAccount(scope.row)" /></div>
            </template></el-table-column>
          <el-table-column label="金额（元）" min-width="210" align="right"><template #default="scope">
              <div class="editable-amount"><span>¥</span><el-input-number v-model="scope.row.amount" :min="0"
                  :precision="2" :step="100" :controls="false" @change="saveAccount(scope.row)" /><el-popconfirm
                  title="确认删除这个资产账户吗？" confirm-button-text="删除" cancel-button-text="取消"
                  @confirm="removeAccount('asset', scope.row.id)"><template #reference><button class="delete-account"
                      :aria-label="`删除${scope.row.account}`"><el-icon>
                        <Delete />
                      </el-icon></button></template></el-popconfirm>
              </div>
            </template></el-table-column>
        </el-table>
      </section>

      <section class="panel ledger-panel liability-ledger">
        <div class="ledger-heading">
          <div><span class="ledger-index">02</span>
            <div>
              <h3>负债账户</h3>
              <p>信用卡及当前应付款项</p>
            </div>
          </div>
          <div class="ledger-actions"><span class="ledger-total">-¥ {{ formatMoney(Math.abs(totalLiabilities))
              }}</span><el-button :icon="Plus" size="small" @click="addAccount('liability')">新增账户</el-button></div>
        </div>
        <el-table v-loading="loading" :data="liabilities">
          <el-table-column label="账户" min-width="180"><template #default="scope">
              <div class="account-name debt"><el-input v-model="scope.row.account" class="account-editor" maxlength="30"
                  @change="saveAccount(scope.row)" /></div>
            </template></el-table-column>
          <el-table-column label="金额（元）" min-width="210" align="right"><template #default="scope">
              <div class="editable-amount"><span>¥</span><el-input-number v-model="scope.row.amount" :max="0"
                  :precision="2" :step="100" :controls="false" @change="saveAccount(scope.row)" /><el-popconfirm
                  title="确认删除这个负债账户吗？" confirm-button-text="删除" cancel-button-text="取消"
                  @confirm="removeAccount('liability', scope.row.id)"><template #reference><button
                      class="delete-account" :aria-label="`删除${scope.row.account}`"><el-icon>
                        <Delete />
                      </el-icon></button></template></el-popconfirm>
              </div>
            </template></el-table-column>
        </el-table>
      </section>
    </div>

  </div>
</template>
