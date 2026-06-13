<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createBackup, listBackups, type Backup } from '@/api/backups'

const backups = ref<Backup[]>([])
const submitting = ref(false)

async function load() {
  const resp = await listBackups()
  backups.value = resp.data
}

async function create() {
  submitting.value = true
  try {
    const resp = await createBackup()
    ElMessage.success(`已创建备份 ${resp.data.filename}`)
    await load()
  } finally {
    submitting.value = false
  }
}

function sizeText(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

onMounted(load)
</script>

<template>
  <div>
    <div style="margin-bottom: 12px">
      <el-button type="primary" :loading="submitting" @click="create">创建备份</el-button>
    </div>
    <el-table :data="backups" stripe>
      <el-table-column prop="filename" label="文件名" />
      <el-table-column label="大小" width="120">
        <template #default="{ row }">{{ sizeText(row.size_bytes) }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="190">
        <template #default="{ row }">
          {{ row.created_at.slice(0, 19).replace('T', ' ') }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
