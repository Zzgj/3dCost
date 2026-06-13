<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getCostSetting, updateCostSetting } from '@/api/settings'
import { listMachines, createMachine, updateMachine, type Machine } from '@/api/machines'
import { listSuppliers, createSupplier, type Supplier } from '@/api/suppliers'

// ---------- 成本参数 ----------
const costForm = reactive({
  electricity_price: '0.65',
  scrap_rate: '0.05',
  labor_rate: '30',
  default_markup: '1.6',
  default_machine_id: null as number | null,
})

async function loadCost() {
  const resp = await getCostSetting()
  const s = resp.data
  costForm.electricity_price = s.electricity_price
  costForm.scrap_rate = s.scrap_rate
  costForm.labor_rate = s.labor_rate
  costForm.default_markup = s.default_markup
  costForm.default_machine_id = s.default_machine_id
}

async function saveCost() {
  await updateCostSetting({
    electricity_price: costForm.electricity_price,
    scrap_rate: costForm.scrap_rate,
    labor_rate: costForm.labor_rate,
    default_markup: costForm.default_markup,
    default_machine_id: costForm.default_machine_id,
  })
  ElMessage.success('成本参数已保存')
}

// ---------- 机器 ----------
const machines = ref<Machine[]>([])
const machineDialog = ref(false)
const machineForm = reactive({ name: '', price: '', life_hours: 10000, power_w: 350 })

async function loadMachines() {
  const resp = await listMachines()
  machines.value = resp.data
}

function openMachineDialog() {
  machineForm.name = ''
  machineForm.price = ''
  machineForm.life_hours = 10000
  machineForm.power_w = 350
  machineDialog.value = true
}

async function submitMachine() {
  await createMachine({
    name: machineForm.name,
    price: machineForm.price,
    life_hours: machineForm.life_hours,
    power_w: machineForm.power_w,
  })
  machineDialog.value = false
  ElMessage.success('机器已创建')
  await loadMachines()
}

async function toggleMachine(m: Machine) {
  await updateMachine(m.id, { is_active: !m.is_active })
  await loadMachines()
}

// ---------- 供应商 ----------
const suppliers = ref<Supplier[]>([])
const supplierDialog = ref(false)
const supplierForm = reactive({ name: '', note: '' })

async function loadSuppliers() {
  const resp = await listSuppliers()
  suppliers.value = resp.data
}

function openSupplierDialog() {
  supplierForm.name = ''
  supplierForm.note = ''
  supplierDialog.value = true
}

async function submitSupplier() {
  await createSupplier({ name: supplierForm.name, note: supplierForm.note || null })
  supplierDialog.value = false
  ElMessage.success('供应商已创建')
  await loadSuppliers()
}

onMounted(() => {
  loadCost()
  loadMachines()
  loadSuppliers()
})
</script>

<template>
  <div>
    <el-tabs>
      <!-- 成本参数 -->
      <el-tab-pane label="成本参数">
        <el-form :model="costForm" label-width="140px" style="max-width: 480px">
          <el-form-item label="电费(元/度)">
            <el-input v-model="costForm.electricity_price" />
          </el-form-item>
          <el-form-item label="废品率">
            <el-input v-model="costForm.scrap_rate">
              <template #append>例 0.05 = 5%</template>
            </el-input>
          </el-form-item>
          <el-form-item label="人工费(元/时)">
            <el-input v-model="costForm.labor_rate" />
          </el-form-item>
          <el-form-item label="默认倍率">
            <el-input v-model="costForm.default_markup" />
          </el-form-item>
          <el-form-item label="默认机器">
            <el-select v-model="costForm.default_machine_id" clearable placeholder="可选">
              <el-option
                v-for="m in machines"
                :key="m.id"
                :label="m.name"
                :value="m.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveCost">保存成本参数</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 机器 -->
      <el-tab-pane label="机器">
        <div style="margin-bottom: 12px">
          <el-button type="primary" @click="openMachineDialog">新建机器</el-button>
        </div>
        <el-table :data="machines" stripe>
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="price" label="购入价(元)" width="120" />
          <el-table-column prop="life_hours" label="寿命(时)" width="120" />
          <el-table-column prop="power_w" label="功率(W)" width="110" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'">
                {{ row.is_active ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button link type="primary" @click="toggleMachine(row)">
                {{ row.is_active ? '停用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 供应商 -->
      <el-tab-pane label="供应商">
        <div style="margin-bottom: 12px">
          <el-button type="primary" @click="openSupplierDialog">新建供应商</el-button>
        </div>
        <el-table :data="suppliers" stripe>
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="note" label="备注" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'">
                {{ row.is_active ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建机器弹窗 -->
    <el-dialog v-model="machineDialog" title="新建机器" width="420px">
      <el-form :model="machineForm" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="machineForm.name" />
        </el-form-item>
        <el-form-item label="购入价(元)">
          <el-input v-model="machineForm.price" />
        </el-form-item>
        <el-form-item label="寿命(时)">
          <el-input-number v-model="machineForm.life_hours" :min="1" />
        </el-form-item>
        <el-form-item label="功率(W)">
          <el-input-number v-model="machineForm.power_w" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="machineDialog = false">取消</el-button>
        <el-button type="primary" @click="submitMachine">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新建供应商弹窗 -->
    <el-dialog v-model="supplierDialog" title="新建供应商" width="420px">
      <el-form :model="supplierForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="supplierForm.name" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="supplierForm.note" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="supplierDialog = false">取消</el-button>
        <el-button type="primary" @click="submitSupplier">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
