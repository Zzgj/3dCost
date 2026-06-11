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
        <el-menu-item index="/purchases">采购记录</el-menu-item>
        <el-menu-item index="/settings">设置</el-menu-item>
      </el-menu>
    </el-aside>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>
