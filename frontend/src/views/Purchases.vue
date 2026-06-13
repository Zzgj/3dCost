<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listMaterials, type Material } from '@/api/materials'
import { listParts, type Part } from '@/api/parts'
import { listSuppliers, type Supplier } from '@/api/suppliers'
import {
  createPurchase,
  listPurchases,
  type Purchase,
  type PurchaseCreate,
} from '@/api/purchases'

const materials = ref<Material[]>([])
const parts = ref<Part[]>([])
const suppliers = ref<Supplier[]>([])

const dialogVisible = ref(false)
const submitting = ref(false)

interface PurchaseForm {
  target_kind: 'material' | 'part'
  target_id: number | null
  qty_rolls: number | null
  grams_per_roll: number | null
  qty: string
  goods_amount: string
  shipping_fee: string
  supplier_id: number | null
  purchase_url: string
}

function emptyForm(): PurchaseForm {
  return {
    target_kind: 'material',
    target_id: null,
    qty_rolls: 1,
    grams_per_roll: 1000,
    qty: '1',
    goods_amount: '',
    shipping_fee: '0',
    supplier_id: null,
    purchase_url: '',
  }
}

const form = ref<PurchaseForm>(emptyForm())

// 查询区
const queryKind = ref<'material' | 'part'>('material')
const queryTargetId = ref<number | null>(null)
const history = ref<Purchase[]>([])

const targetOptions = computed(() =>
  form.value.target_kind === 'material' ? materials.value : parts.value,
)
const queryOptions = computed(() =>
  queryKind.value === 'material' ? materials.value : parts.value,
)

async function loadBasics() {
  const [m, p, s] = await Promise.all([
    listMaterials(1, 100),
    listParts(1, 100),
    listSuppliers(1, 100),
  ])
  materials.value = m.data
  parts.value = p.data
  suppliers.value = s.data
}

function openDialog() {
  form.value = emptyForm()
  dialogVisible.value = true
}

function onKindChange() {
  form.value.target_id = null
}

async function submit() {
  if (!form.value.target_id) {
    ElMessage.warning('请选择采购对象')
    return
  }
  if (!form.value.goods_amount) {
    ElMessage.warning('请填写货款金额')
    return
  }
  const payload: PurchaseCreate = {
    target_kind: form.value.target_kind,
    target_id: form.value.target_id,
    goods_amount: form.value.goods_amount,
    shipping_fee: form.value.shipping_fee || '0',
    supplier_id: form.value.supplier_id,
    purchase_url: form.value.purchase_url || null,
  }
  if (form.value.target_kind === 'material') {
    payload.qty_rolls = form.value.qty_rolls ?? undefined
    payload.grams_per_roll = form.value.grams_per_roll ?? undefined
  } else {
    payload.qty = form.value.qty
  }
  submitting.value = true
  try {
    const resp = await createPurchase(payload)
    ElMessage.success(
      `已入库，最新到手价 ${resp.data.updated_avg_price}，库存 ${resp.data.total_stock}`,
    )
    dialogVisible.value = false
    await loadBasics()
    // 若查询区正看着同一对象，刷新历史
    if (
      queryKind.value === payload.target_kind &&
      queryTargetId.value === payload.target_id
    ) {
      await loadHistory()
    }
  } finally {
    submitting.value = false
  }
}

async function loadHistory() {
  if (!queryTargetId.value) {
    history.value = []
    return
  }
  const resp = await listPurchases(queryKind.value, queryTargetId.value)
  history.value = resp.data
}

function onQueryKindChange() {
  queryTargetId.value = null
  history.value = []
}

onMounted(loadBasics)
</script>

<template>
  <div>
    <div style="margin-bottom: 16px">
      <el-button type="primary" @click="openDialog">录入采购</el-button>
    </div>

    <el-card shadow="never" style="margin-bottom: 16px">
      <template #header>查询采购历史</template>
      <el-form inline>
        <el-form-item label="类型">
          <el-radio-group v-model="queryKind" @change="onQueryKindChange">
            <el-radio-button value="material">耗材</el-radio-button>
            <el-radio-button value="part">零件</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="对象">
          <el-select
            v-model="queryTargetId"
            placeholder="选择"
            style="width: 220px"
            filterable
            @change="loadHistory"
          >
            <el-option
              v-for="o in queryOptions"
              :key="o.id"
              :label="o.name"
              :value="o.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <el-table :data="history" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="数量">
          <template #default="{ row }">
            <span v-if="row.target_kind === 'material'">
              {{ row.qty_rolls }} 卷 × {{ row.grams_per_roll }}g
            </span>
            <span v-else>{{ row.qty }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="goods_amount" label="货款" width="110" />
        <el-table-column prop="shipping_fee" label="运费" width="100" />
        <el-table-column prop="purchased_at" label="采购时间">
          <template #default="{ row }">
            {{ row.purchased_at?.slice(0, 19).replace('T', ' ') }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="录入采购" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="类型">
          <el-radio-group v-model="form.target_kind" @change="onKindChange">
            <el-radio-button value="material">耗材</el-radio-button>
            <el-radio-button value="part">零件</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="对象">
          <el-select v-model="form.target_id" placeholder="选择" filterable style="width: 100%">
            <el-option
              v-for="o in targetOptions"
              :key="o.id"
              :label="o.name"
              :value="o.id"
            />
          </el-select>
        </el-form-item>

        <template v-if="form.target_kind === 'material'">
          <el-form-item label="卷数">
            <el-input-number v-model="form.qty_rolls" :min="1" />
          </el-form-item>
          <el-form-item label="每卷克数">
            <el-input-number v-model="form.grams_per_roll" :min="1" :step="100" />
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item label="数量">
            <el-input v-model="form.qty" />
          </el-form-item>
        </template>

        <el-form-item label="货款金额">
          <el-input v-model="form.goods_amount">
            <template #append>元</template>
          </el-input>
        </el-form-item>
        <el-form-item label="运费">
          <el-input v-model="form.shipping_fee">
            <template #append>元</template>
          </el-input>
        </el-form-item>
        <el-form-item label="供应商">
          <el-select v-model="form.supplier_id" placeholder="可选" clearable style="width: 100%">
            <el-option
              v-for="s in suppliers"
              :key="s.id"
              :label="s.name"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="采购链接">
          <el-input v-model="form.purchase_url" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
