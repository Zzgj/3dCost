<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listMaterials, createMaterial, type Material } from '@/api/materials'

const materials = ref<Material[]>([])
const total = ref(0)
const dialogVisible = ref(false)
const form = ref({ name: '', type: 'PLA' })

async function load() {
  const resp = await listMaterials()
  materials.value = resp.data
  total.value = resp.pagination.total
}

async function submit() {
  await createMaterial({ name: form.value.name, type: form.value.type })
  dialogVisible.value = false
  form.value = { name: '', type: 'PLA' }
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <div style="margin-bottom: 12px">
      <el-button type="primary" @click="dialogVisible = true">新建耗材</el-button>
    </div>
    <el-table :data="materials" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column prop="stock_g" label="库存(g)" width="120" />
      <el-table-column prop="avg_price_per_g" label="到手价(元/g)" width="140" />
    </el-table>

    <el-dialog v-model="dialogVisible" title="新建耗材" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-input v-model="form.type" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
