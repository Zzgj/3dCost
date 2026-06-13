<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import {
  getLowStock,
  getMaterialUsage,
  getMonthlyStats,
  type LowStock,
  type MaterialUsage,
  type MonthlyStats,
} from '@/api/stats'

const today = new Date()
const query = reactive({ year: today.getFullYear(), month: today.getMonth() + 1 })
const lowStock = ref<LowStock>({ materials: [], parts: [] })
const monthly = ref<MonthlyStats | null>(null)
const usage = ref<MaterialUsage[]>([])

async function load() {
  const [low, mon, use] = await Promise.all([
    getLowStock(),
    getMonthlyStats(query.year, query.month),
    getMaterialUsage(),
  ])
  lowStock.value = low.data
  monthly.value = mon.data
  usage.value = use.data
}

onMounted(load)
</script>

<template>
  <div>
    <el-form inline style="margin-bottom: 12px">
      <el-form-item label="年份">
        <el-input-number v-model="query.year" :min="2000" :max="2100" />
      </el-form-item>
      <el-form-item label="月份">
        <el-input-number v-model="query.month" :min="1" :max="12" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="load">刷新</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="12" style="margin-bottom: 16px">
      <el-col :span="6">
        <el-statistic title="产品数" :value="monthly?.products_count ?? 0" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="已完成" :value="monthly?.completed_count ?? 0" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="总成本" :value="monthly?.total_cost ?? '0.00'" suffix="元" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="预估利润" :value="monthly?.estimated_profit ?? '0.00'" suffix="元" />
      </el-col>
    </el-row>

    <el-tabs>
      <el-tab-pane label="低库存">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-table :data="lowStock.materials" stripe>
              <el-table-column prop="name" label="耗材" />
              <el-table-column prop="stock_g" label="库存(g)" width="110" />
              <el-table-column prop="low_stock_g" label="阈值(g)" width="110" />
            </el-table>
          </el-col>
          <el-col :span="12">
            <el-table :data="lowStock.parts" stripe>
              <el-table-column prop="name" label="零件" />
              <el-table-column label="库存" width="120">
                <template #default="{ row }">{{ row.stock_qty }} {{ row.use_unit }}</template>
              </el-table-column>
              <el-table-column prop="low_stock_qty" label="阈值" width="100" />
            </el-table>
          </el-col>
        </el-row>
      </el-tab-pane>
      <el-tab-pane label="耗材消耗">
        <el-table :data="usage" stripe>
          <el-table-column prop="material_name" label="耗材" />
          <el-table-column prop="grams" label="已完成产品用量(g)" width="180" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
