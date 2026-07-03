<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { Check, Delete, Plus, RefreshRight } from '@element-plus/icons-vue'

interface AccountItem {
  id: number
  account: string
  amount: number
}

const lastUpdated = ref('刚刚')
const assets = reactive<AccountItem[]>([
  { id: 1, account: '微信', amount: 68247.16 },
  { id: 2, account: '支付宝', amount: 2260.64 },
  { id: 3, account: '同花顺', amount: 8981.59 },
  { id: 4, account: '押金', amount: 3000 },
  { id: 5, account: '银行卡', amount: 60 },
])
const liabilities = reactive<AccountItem[]>([
  { id: 6, account: '招商银行', amount: -105.85 },
  { id: 7, account: '平安银行', amount: -175.7 },
  { id: 8, account: '美团', amount: -133 },
  { id: 9, account: '京东', amount: -306 },
  { id: 10, account: '花呗', amount: -185.42 },
])

const totalAssets = computed(() => assets.reduce((total, item) => total + Number(item.amount || 0), 0))
const totalLiabilities = computed(() => liabilities.reduce((total, item) => total + Number(item.amount || 0), 0))
const netAssets = computed(() => totalAssets.value + totalLiabilities.value)
const liabilityRatio = computed(() => totalAssets.value ? (Math.abs(totalLiabilities.value) / totalAssets.value) * 100 : 0)

const formatMoney = (value: number) => new Intl.NumberFormat('zh-CN', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}).format(value)

const markUpdated = () => {
  lastUpdated.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const addAccount = (type: 'asset' | 'liability') => {
  const nextId = Math.max(0, ...assets.map((item) => item.id), ...liabilities.map((item) => item.id)) + 1
  const target = type === 'asset' ? assets : liabilities
  target.push({ id: nextId, account: type === 'asset' ? '新资产账户' : '新负债账户', amount: 0 })
  markUpdated()
}

const removeAccount = (type: 'asset' | 'liability', id: number) => {
  const target = type === 'asset' ? assets : liabilities
  const index = target.findIndex((item) => item.id === id)
  if (index !== -1) target.splice(index, 1)
  markUpdated()
}

const resetDemoData = () => {
  assets.splice(0, assets.length,
    { id: 1, account: '微信', amount: 68247.16 },
    { id: 2, account: '支付宝', amount: 2260.64 },
    { id: 3, account: '同花顺', amount: 8981.59 },
    { id: 4, account: '押金', amount: 3000 },
    { id: 5, account: '银行卡', amount: 60 },
  )
  liabilities.splice(0, liabilities.length,
    { id: 6, account: '招商银行', amount: -105.85 },
    { id: 7, account: '平安银行', amount: -175.7 },
    { id: 8, account: '美团', amount: -133 },
    { id: 9, account: '京东', amount: -306 },
    { id: 10, account: '花呗', amount: -185.42 },
  )
  markUpdated()
}
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

    <section class="asset-overview">
      <article class="asset-stat total">
        <div class="asset-stat-heading"><span>总资产</span><small>ASSETS</small></div>
        <strong><i>¥</i>{{ formatMoney(totalAssets) }}</strong>
        <div class="asset-stat-foot"><span>共 {{ assets.length }} 个资产账户</span><i></i></div>
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
        <el-table :data="assets">
          <el-table-column label="账户" min-width="180"><template #default="scope">
              <div class="account-name"><el-input v-model="scope.row.account" class="account-editor" maxlength="30"
                  @change="markUpdated" /></div>
            </template></el-table-column>
          <el-table-column label="金额（元）" min-width="210" align="right"><template #default="scope">
              <div class="editable-amount"><span>¥</span><el-input-number v-model="scope.row.amount" :min="0"
                  :precision="2" :step="100" :controls="false" @change="markUpdated" /><el-popconfirm
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
        <el-table :data="liabilities">
          <el-table-column label="账户" min-width="180"><template #default="scope">
              <div class="account-name debt"><el-input v-model="scope.row.account" class="account-editor" maxlength="30"
                  @change="markUpdated" /></div>
            </template></el-table-column>
          <el-table-column label="金额（元）" min-width="210" align="right"><template #default="scope">
              <div class="editable-amount"><span>¥</span><el-input-number v-model="scope.row.amount" :max="0"
                  :precision="2" :step="100" :controls="false" @change="markUpdated" /><el-popconfirm
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

    <button class="asset-reset" @click="resetDemoData"><el-icon>
        <RefreshRight />
      </el-icon>恢复初始数据</button>
  </div>
</template>
