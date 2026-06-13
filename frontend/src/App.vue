<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()
const active = ref(route.path)

function go(path: string) {
  active.value = path
  router.push(path)
}
</script>

<template>
  <el-container style="height: 100vh">
    <el-aside width="200px">
      <el-menu :default-active="active" @select="go">
        <el-menu-item index="/inventory">仓储管理</el-menu-item>
        <el-menu-item index="/purchases">采购录入</el-menu-item>
        <el-menu-item index="/print-items">打印件</el-menu-item>
        <el-menu-item index="/products">产品报价</el-menu-item>
        <el-menu-item index="/quotes">报价历史</el-menu-item>
        <el-menu-item index="/dashboard">统计看板</el-menu-item>
        <el-menu-item index="/backups">数据备份</el-menu-item>
        <el-menu-item index="/settings">设置</el-menu-item>
      </el-menu>
    </el-aside>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>
