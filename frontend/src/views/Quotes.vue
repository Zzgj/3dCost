<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listProducts, type ProductDetail } from '@/api/products'
import { getQuote, listQuotes, quoteExportUrl, type Quote, type QuoteDetail } from '@/api/quotes'

const quotes = ref<Quote[]>([])
const products = ref<ProductDetail[]>([])
const selectedProduct = ref<number | null>(null)
const detailVisible = ref(false)
const current = ref<QuoteDetail | null>(null)

async function load() {
  const [q, p] = await Promise.all([
    listQuotes(1, 100, selectedProduct.value),
    listProducts(1, 100),
  ])
  quotes.value = q.data
  products.value = p.data
}

async function showDetail(row: Quote) {
  const resp = await getQuote(row.id)
  current.value = resp.data
  detailVisible.value = true
}

function openExport(row: Quote, type: 'internal' | 'customer') {
  window.open(quoteExportUrl(row.id, type), '_blank')
}

onMounted(load)
</script>

<template>
  <div>
    <el-form inline style="margin-bottom: 12px">
      <el-form-item label="产品">
        <el-select
          v-model="selectedProduct"
          clearable
          filterable
          placeholder="全部产品"
          style="width: 260px"
          @change="load"
        >
          <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button @click="load">刷新</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="quotes" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="product_id" label="产品ID" width="90" />
      <el-table-column prop="mode" label="模式" width="90" />
      <el-table-column prop="internal_cost" label="内部成本" width="120" />
      <el-table-column label="客户报价" width="130">
        <template #default="{ row }">
          <el-text type="primary" tag="b">{{ row.customer_price }}</el-text>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="生成时间">
        <template #default="{ row }">
          {{ row.created_at.slice(0, 19).replace('T', ' ') }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button link type="primary" @click="showDetail(row)">明细</el-button>
          <el-button link type="primary" @click="openExport(row, 'internal')">对内版</el-button>
          <el-button link type="success" @click="openExport(row, 'customer')">客户版</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="detailVisible" title="报价快照" width="760px">
      <template v-if="current">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="产品">
            {{ current.snapshot.product.name }}
          </el-descriptions-item>
          <el-descriptions-item label="模式">{{ current.mode }}</el-descriptions-item>
          <el-descriptions-item label="内部成本">
            {{ current.internal_cost }}
          </el-descriptions-item>
          <el-descriptions-item label="客户报价">
            <el-text type="primary" tag="b">{{ current.customer_price }}</el-text>
          </el-descriptions-item>
        </el-descriptions>
        <el-divider content-position="left">BOM 快照</el-divider>
        <el-table :data="current.snapshot.bom_items" size="small" stripe>
          <el-table-column prop="kind_label" label="类型" width="110" />
          <el-table-column prop="ref_name" label="项目" min-width="140" />
          <el-table-column label="数量/工时" width="110">
            <template #default="{ row }">{{ row.qty || row.hours || '-' }}</template>
          </el-table-column>
          <el-table-column prop="unit_price" label="单价" width="100" />
          <el-table-column prop="subtotal" label="小计" width="100" />
        </el-table>
      </template>
    </el-dialog>
  </div>
</template>
