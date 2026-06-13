<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  listPrintItems,
  createPrintItem,
  deletePrintItem,
  type PrintItem,
} from '@/api/printItems'
import { listMachines, type Machine } from '@/api/machines'
import { listMaterials, type Material } from '@/api/materials'

const items = ref<PrintItem[]>([])
const machines = ref<Machine[]>([])
const materials = ref<Material[]>([])

const dialogVisible = ref(false)
const form = reactive({
  name: '',
  machine_id: null as number | null,
  print_hours: '1',
  plates: 1,
  nozzle: '0.4mm',
  source_url: '',
  filaments: [{ material_id: null as number | null, grams: '' }],
})

function machineName(id: number) {
  return machines.value.find((m) => m.id === id)?.name ?? `#${id}`
}

async function load() {
  const [pi, mac, mat] = await Promise.all([
    listPrintItems(1, 100),
    listMachines(),
    listMaterials(1, 100),
  ])
  items.value = pi.data
  machines.value = mac.data
  materials.value = mat.data
}

function openDialog() {
  form.name = ''
  form.machine_id = machines.value[0]?.id ?? null
  form.print_hours = '1'
  form.plates = 1
  form.nozzle = '0.4mm'
  form.source_url = ''
  form.filaments = [{ material_id: materials.value[0]?.id ?? null, grams: '' }]
  dialogVisible.value = true
}

function addFilament() {
  form.filaments.push({ material_id: materials.value[0]?.id ?? null, grams: '' })
}

function removeFilament(idx: number) {
  form.filaments.splice(idx, 1)
}

async function submit() {
  if (!form.machine_id) {
    ElMessage.warning('请选择机器')
    return
  }
  const filaments = form.filaments
    .filter((f) => f.material_id && f.grams)
    .map((f) => ({ material_id: f.material_id as number, grams: f.grams }))
  if (filaments.length === 0) {
    ElMessage.warning('至少录入一项耗材')
    return
  }
  await createPrintItem({
    name: form.name,
    machine_id: form.machine_id,
    print_hours: form.print_hours,
    plates: form.plates,
    nozzle: form.nozzle,
    source_url: form.source_url || null,
    filaments,
  })
  dialogVisible.value = false
  ElMessage.success('打印件已创建')
  await load()
}

async function remove(item: PrintItem) {
  await deletePrintItem(item.id)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div style="margin-bottom: 12px">
      <el-button type="primary" @click="openDialog">新建打印件</el-button>
      <el-text v-if="machines.length === 0" type="warning" style="margin-left: 12px">
        请先在「设置 - 机器」中创建机器
      </el-text>
    </div>

    <el-table :data="items" stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column label="机器" width="120">
        <template #default="{ row }">{{ machineName(row.machine_id) }}</template>
      </el-table-column>
      <el-table-column prop="print_hours" label="打印时长(时)" width="120" />
      <el-table-column label="耗材费" width="110">
        <template #default="{ row }">
          {{ row.cost ? row.cost.material_cost : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="机时费" width="110">
        <template #default="{ row }">
          {{ row.cost ? row.cost.machine_cost : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="成本合计" width="120">
        <template #default="{ row }">
          <el-text v-if="row.cost" type="primary" tag="b">{{ row.cost.total }}</el-text>
          <el-tooltip v-else content="缺少成本数据（机器停用或缺失）">
            <el-tag type="danger">无法核算</el-tag>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90">
        <template #default="{ row }">
          <el-popconfirm title="确认删除该打印件?" @confirm="remove(row)">
            <template #reference>
              <el-button link type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新建打印件" width="640px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="机器">
          <el-select v-model="form.machine_id" placeholder="选择机器">
            <el-option v-for="m in machines" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="打印时长(时)">
          <el-input v-model="form.print_hours" />
        </el-form-item>
        <el-form-item label="盘数">
          <el-input-number v-model="form.plates" :min="1" />
        </el-form-item>
        <el-form-item label="喷嘴">
          <el-input v-model="form.nozzle" />
        </el-form-item>
        <el-form-item label="来源链接">
          <el-input v-model="form.source_url" placeholder="可选" />
        </el-form-item>

        <el-divider content-position="left">耗材用量</el-divider>
        <div
          v-for="(f, idx) in form.filaments"
          :key="idx"
          style="display: flex; gap: 8px; margin-bottom: 8px; align-items: center"
        >
          <el-select v-model="f.material_id" placeholder="耗材" style="width: 220px">
            <el-option
              v-for="mat in materials"
              :key="mat.id"
              :label="`${mat.name}（${mat.avg_price_per_g}元/g）`"
              :value="mat.id"
            />
          </el-select>
          <el-input v-model="f.grams" placeholder="克数" style="width: 140px">
            <template #append>g</template>
          </el-input>
          <el-button
            link
            type="danger"
            :disabled="form.filaments.length === 1"
            @click="removeFilament(idx)"
          >
            移除
          </el-button>
        </div>
        <el-button link type="primary" @click="addFilament">+ 添加耗材</el-button>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
