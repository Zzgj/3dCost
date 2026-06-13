<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  listProducts,
  createProduct,
  updateProduct,
  consumeStock,
  completeProduct,
  type ProductDetail,
  type BOMKind,
  type BOMItemIn,
} from '@/api/products'
import { listPrintItems, type PrintItem } from '@/api/printItems'
import { listParts, type Part } from '@/api/parts'
import { createQuote } from '@/api/quotes'

const products = ref<ProductDetail[]>([])
const printItems = ref<PrintItem[]>([])
const parts = ref<Part[]>([])

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const detailVisible = ref(false)
const current = ref<ProductDetail | null>(null)

interface BomRow {
  kind: BOMKind
  ref_id: number | null
  qty: string
  hours: string
}

const form = reactive({
  name: '',
  note: '',
  mode: 'estimate',
  markup_rate: '1.6',
  bom: [] as BomRow[],
})

const kindOptions = [
  { value: 'printitem', label: '打印件' },
  { value: 'part', label: '零件' },
  { value: 'postprocess', label: '后处理(工时)' },
  { value: 'subproduct', label: '子产品' },
]

function kindLabel(kind: string) {
  return kindOptions.find((k) => k.value === kind)?.label ?? kind
}

const dialogTitle = computed(() => (editingId.value ? '编辑产品' : '新建产品'))

async function load() {
  const [prod, pi, pt] = await Promise.all([
    listProducts(1, 100),
    listPrintItems(1, 100),
    listParts(1, 100),
  ])
  products.value = prod.data
  printItems.value = pi.data
  parts.value = pt.data
}

function refOptions(kind: BOMKind) {
  if (kind === 'printitem') {
    return printItems.value.map((p) => ({ value: p.id, label: p.name }))
  }
  if (kind === 'part') {
    return parts.value.map((p) => ({ value: p.id, label: p.name }))
  }
  if (kind === 'subproduct') {
    return products.value.map((p) => ({ value: p.id, label: p.name }))
  }
  return []
}

function openCreate() {
  editingId.value = null
  form.name = ''
  form.note = ''
  form.mode = 'estimate'
  form.markup_rate = '1.6'
  form.bom = []
  dialogVisible.value = true
}

function openEdit(p: ProductDetail) {
  if (p.status === 'completed') {
    ElMessage.warning('已完成的产品已锁定，无法编辑')
    return
  }
  editingId.value = p.id
  form.name = p.name
  form.note = p.note ?? ''
  form.mode = p.mode
  form.markup_rate = p.markup_rate
  form.bom = p.bom_items.map((it) => ({
    kind: it.kind,
    ref_id: it.ref_id,
    qty: it.qty ?? '1',
    hours: it.hours ?? '0',
  }))
  dialogVisible.value = true
}

function addBomRow() {
  form.bom.push({ kind: 'printitem', ref_id: null, qty: '1', hours: '0' })
}

function removeBomRow(idx: number) {
  form.bom.splice(idx, 1)
}

function buildBomPayload(): BOMItemIn[] {
  return form.bom.map((row) => {
    if (row.kind === 'postprocess') {
      return { kind: row.kind, hours: row.hours }
    }
    return { kind: row.kind, ref_id: row.ref_id, qty: row.qty }
  })
}

async function submit() {
  const bom_items = buildBomPayload()
  if (editingId.value) {
    await updateProduct(editingId.value, {
      name: form.name,
      note: form.note || null,
      mode: form.mode,
      markup_rate: form.markup_rate,
      bom_items,
    })
    ElMessage.success('已更新')
  } else {
    await createProduct({
      name: form.name,
      note: form.note || null,
      mode: form.mode,
      markup_rate: form.markup_rate,
      bom_items,
    })
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  await load()
}

function showDetail(p: ProductDetail) {
  current.value = p
  detailVisible.value = true
}

async function doConsume(p: ProductDetail) {
  const resp = await consumeStock(p.id)
  const c = resp.data.consumed
  ElMessage.success(`已扣减 ${c.materials.length} 项耗材、${c.parts.length} 项零件`)
  if (resp.data.warnings.length) {
    ElMessage.warning(resp.data.warnings.join('；'))
  }
  await load()
}

async function doComplete(p: ProductDetail) {
  await completeProduct(p.id)
  ElMessage.success('产品已完成并锁定')
  await load()
}

async function doCreateQuote(p: ProductDetail) {
  const resp = await createQuote(p.id, p.mode)
  ElMessage.success(`已生成报价快照 #${resp.data.id}`)
}

onMounted(load)
</script>

<template>
  <div>
    <div style="margin-bottom: 12px">
      <el-button type="primary" @click="openCreate">新建产品</el-button>
    </div>

    <el-table :data="products" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'completed' ? 'success' : 'info'">
            {{ row.status === 'completed' ? '已完成' : '草稿' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="markup_rate" label="倍率" width="80" />
      <el-table-column prop="total_cost" label="总成本" width="110" />
      <el-table-column label="报价" width="120">
        <template #default="{ row }">
          <el-text type="primary" tag="b">{{ row.customer_price }}</el-text>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="340">
        <template #default="{ row }">
          <el-button link type="primary" @click="showDetail(row)">明细</el-button>
          <el-button
            link
            type="primary"
            :disabled="row.status === 'completed'"
            @click="openEdit(row)"
          >
            编辑
          </el-button>
          <el-popconfirm title="按 BOM 扣减库存?" @confirm="doConsume(row)">
            <template #reference>
              <el-button link type="warning">扣减库存</el-button>
            </template>
          </el-popconfirm>
          <el-button link type="success" @click="doCreateQuote(row)">生成报价</el-button>
          <el-popconfirm
            v-if="row.status !== 'completed'"
            title="标记完成将锁定产品?"
            @confirm="doComplete(row)"
          >
            <template #reference>
              <el-button link type="success">完成</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="760px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" placeholder="可选" />
        </el-form-item>
        <el-form-item label="模式">
          <el-radio-group v-model="form.mode">
            <el-radio value="estimate">预估</el-radio>
            <el-radio value="actual">实际</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="倍率">
          <el-input v-model="form.markup_rate" style="width: 160px" />
        </el-form-item>

        <el-divider content-position="left">BOM 清单</el-divider>
        <div
          v-for="(row, idx) in form.bom"
          :key="idx"
          style="display: flex; gap: 8px; margin-bottom: 8px; align-items: center"
        >
          <el-select v-model="row.kind" style="width: 150px">
            <el-option v-for="k in kindOptions" :key="k.value" :label="k.label" :value="k.value" />
          </el-select>
          <el-select
            v-if="row.kind !== 'postprocess'"
            v-model="row.ref_id"
            placeholder="选择项目"
            style="width: 240px"
          >
            <el-option
              v-for="o in refOptions(row.kind)"
              :key="o.value"
              :label="o.label"
              :value="o.value"
            />
          </el-select>
          <el-input
            v-if="row.kind !== 'postprocess'"
            v-model="row.qty"
            placeholder="数量"
            style="width: 120px"
          >
            <template #prepend>数量</template>
          </el-input>
          <el-input v-else v-model="row.hours" placeholder="工时" style="width: 160px">
            <template #prepend>工时</template>
          </el-input>
          <el-button link type="danger" @click="removeBomRow(idx)">移除</el-button>
        </div>
        <el-button link type="primary" @click="addBomRow">+ 添加 BOM 项</el-button>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 成本明细 -->
    <el-dialog v-model="detailVisible" title="成本明细" width="720px">
      <template v-if="current">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">{{ current.name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            {{ current.status === 'completed' ? '已完成' : '草稿' }}
          </el-descriptions-item>
          <el-descriptions-item label="打印件成本">
            {{ current.cost_detail.printitems_cost }}
          </el-descriptions-item>
          <el-descriptions-item label="零件成本">
            {{ current.cost_detail.parts_cost }}
          </el-descriptions-item>
          <el-descriptions-item label="后处理成本">
            {{ current.cost_detail.postprocess_cost }}
          </el-descriptions-item>
          <el-descriptions-item label="子产品成本">
            {{ current.cost_detail.subproduct_cost }}
          </el-descriptions-item>
          <el-descriptions-item label="小计">
            {{ current.cost_detail.subtotal }}
          </el-descriptions-item>
          <el-descriptions-item label="废品成本">
            {{ current.cost_detail.scrap_cost }}
          </el-descriptions-item>
          <el-descriptions-item label="总成本">
            <el-text tag="b">{{ current.cost_detail.total_cost }}</el-text>
          </el-descriptions-item>
          <el-descriptions-item label="客户报价">
            <el-text type="primary" tag="b">{{ current.cost_detail.customer_price }}</el-text>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">BOM 明细</el-divider>
        <el-table :data="current.bom_items" stripe size="small">
          <el-table-column label="类型" width="120">
            <template #default="{ row }">{{ kindLabel(row.kind) }}</template>
          </el-table-column>
          <el-table-column prop="ref_name" label="项目" min-width="140">
            <template #default="{ row }">{{ row.ref_name ?? '-' }}</template>
          </el-table-column>
          <el-table-column label="数量/工时" width="100">
            <template #default="{ row }">
              {{ row.kind === 'postprocess' ? row.hours : row.qty }}
            </template>
          </el-table-column>
          <el-table-column prop="unit_price" label="单价" width="100" />
          <el-table-column prop="subtotal" label="小计" width="100" />
        </el-table>
      </template>
    </el-dialog>
  </div>
</template>
