<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { listMaterials, createMaterial, type Material } from '@/api/materials'
import { listParts, createPart, type Part } from '@/api/parts'

const tab = ref('materials')

// ---------- 耗材 ----------
const materials = ref<Material[]>([])
const matDialog = ref(false)
const matForm = ref({ name: '', type: 'PLA', color: '', brand: '', low_stock_g: '' })

async function loadMaterials() {
  const resp = await listMaterials(1, 100)
  materials.value = resp.data
}

async function submitMaterial() {
  if (!matForm.value.name.trim()) {
    ElMessage.warning('请填写名称')
    return
  }
  await createMaterial({
    name: matForm.value.name,
    type: matForm.value.type,
    color: matForm.value.color || undefined,
    brand: matForm.value.brand || undefined,
    low_stock_g: matForm.value.low_stock_g || undefined,
  })
  matDialog.value = false
  matForm.value = { name: '', type: 'PLA', color: '', brand: '', low_stock_g: '' }
  ElMessage.success('已创建')
  await loadMaterials()
}

// ---------- 零件 ----------
const parts = ref<Part[]>([])
const partDialog = ref(false)
const partForm = ref({
  name: '',
  category: '',
  spec: '',
  purchase_unit: '个',
  use_unit: '个',
  conversion_ratio: '1',
  low_stock_qty: '',
})

async function loadParts() {
  const resp = await listParts(1, 100)
  parts.value = resp.data
}

async function submitPart() {
  if (!partForm.value.name.trim()) {
    ElMessage.warning('请填写名称')
    return
  }
  await createPart({
    name: partForm.value.name,
    category: partForm.value.category || undefined,
    spec: partForm.value.spec || undefined,
    purchase_unit: partForm.value.purchase_unit || undefined,
    use_unit: partForm.value.use_unit || undefined,
    conversion_ratio: partForm.value.conversion_ratio || undefined,
    low_stock_qty: partForm.value.low_stock_qty || undefined,
  })
  partDialog.value = false
  partForm.value = {
    name: '',
    category: '',
    spec: '',
    purchase_unit: '个',
    use_unit: '个',
    conversion_ratio: '1',
    low_stock_qty: '',
  }
  ElMessage.success('已创建')
  await loadParts()
}

function lowMaterial(m: Material) {
  return Number(m.stock_g) < Number(m.low_stock_g)
}
function lowPart(p: Part) {
  return Number(p.stock_qty) < Number(p.low_stock_qty)
}

onMounted(() => {
  loadMaterials()
  loadParts()
})
</script>

<template>
  <div>
    <el-tabs v-model="tab">
      <el-tab-pane label="耗材" name="materials">
        <div style="margin-bottom: 12px">
          <el-button type="primary" @click="matDialog = true">新建耗材</el-button>
        </div>
        <el-table :data="materials" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="type" label="类型" width="90" />
          <el-table-column prop="color" label="颜色" width="90" />
          <el-table-column prop="brand" label="品牌" width="110" />
          <el-table-column label="库存(g)" width="130">
            <template #default="{ row }">
              <span :style="lowMaterial(row) ? 'color:#f56c6c;font-weight:600' : ''">
                {{ row.stock_g }}
              </span>
              <el-tag v-if="lowMaterial(row)" type="danger" size="small" style="margin-left: 6px">
                低
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="low_stock_g" label="阈值(g)" width="100" />
          <el-table-column prop="avg_price_per_g" label="到手价(元/g)" width="130" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="零件" name="parts">
        <div style="margin-bottom: 12px">
          <el-button type="primary" @click="partDialog = true">新建零件</el-button>
        </div>
        <el-table :data="parts" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column prop="spec" label="规格" width="120" />
          <el-table-column label="库存" width="130">
            <template #default="{ row }">
              <span :style="lowPart(row) ? 'color:#f56c6c;font-weight:600' : ''">
                {{ row.stock_qty }} {{ row.use_unit }}
              </span>
              <el-tag v-if="lowPart(row)" type="danger" size="small" style="margin-left: 6px">
                低
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="low_stock_qty" label="阈值" width="90" />
          <el-table-column prop="avg_unit_price" label="到手价(元)" width="120" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建耗材 -->
    <el-dialog v-model="matDialog" title="新建耗材" width="440px">
      <el-form :model="matForm" label-width="90px">
        <el-form-item label="名称" required>
          <el-input v-model="matForm.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-input v-model="matForm.type" placeholder="PLA / PETG / ABS ..." />
        </el-form-item>
        <el-form-item label="颜色">
          <el-input v-model="matForm.color" />
        </el-form-item>
        <el-form-item label="品牌">
          <el-input v-model="matForm.brand" />
        </el-form-item>
        <el-form-item label="低库存阈值">
          <el-input v-model="matForm.low_stock_g" placeholder="克数，留空为 0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="matDialog = false">取消</el-button>
        <el-button type="primary" @click="submitMaterial">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新建零件 -->
    <el-dialog v-model="partDialog" title="新建零件" width="440px">
      <el-form :model="partForm" label-width="90px">
        <el-form-item label="名称" required>
          <el-input v-model="partForm.name" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="partForm.category" />
        </el-form-item>
        <el-form-item label="规格">
          <el-input v-model="partForm.spec" />
        </el-form-item>
        <el-form-item label="采购单位">
          <el-input v-model="partForm.purchase_unit" />
        </el-form-item>
        <el-form-item label="使用单位">
          <el-input v-model="partForm.use_unit" />
        </el-form-item>
        <el-form-item label="换算比">
          <el-input v-model="partForm.conversion_ratio" placeholder="1 采购单位 = ? 使用单位" />
        </el-form-item>
        <el-form-item label="低库存阈值">
          <el-input v-model="partForm.low_stock_qty" placeholder="留空为 0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="partDialog = false">取消</el-button>
        <el-button type="primary" @click="submitPart">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
