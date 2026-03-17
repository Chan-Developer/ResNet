<template>
  <div class="uploader-wrap">
    <el-upload
      :auto-upload="false"
      :multiple="multiple"
      :limit="limit"
      :on-change="handleChange"
      :on-remove="handleRemove"
      :on-exceed="handleExceed"
      :file-list="fileList"
      list-type="picture-card"
      accept="image/*"
      drag
      class="cute-upload"
    >
      <div class="upload-inner">
        <span class="upload-icon">+</span>
        <span class="upload-text">点击或拖拽上传</span>
      </div>
      <template #tip>
        <div class="upload-tip">
          支持 JPG / PNG 格式{{ multiple ? `，最多 ${limit} 张` : '' }}
        </div>
      </template>
    </el-upload>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile, UploadFiles } from 'element-plus'

const props = withDefaults(defineProps<{
  multiple?: boolean
  limit?: number
}>(), {
  multiple: false,
  limit: 1,
})

const emit = defineEmits<{
  change: [files: File[]]
}>()

const fileList = ref<UploadFile[]>([])

function handleChange(_file: UploadFile, files: UploadFiles) {
  if (!props.multiple) {
    fileList.value = files.slice(-1)
  } else {
    fileList.value = files
  }
  emitFiles()
}

function handleRemove(_file: UploadFile, files: UploadFiles) {
  fileList.value = files
  emitFiles()
}

function handleExceed() {
  ElMessage.warning(`最多上传 ${props.limit} 张图片`)
}

function emitFiles() {
  const raw = fileList.value
    .map((f) => f.raw)
    .filter(Boolean) as File[]
  emit('change', raw)
}
</script>

<style scoped>
.uploader-wrap {
  margin-bottom: 8px;
}
.upload-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.upload-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--lavender-light);
  color: var(--pink-deep);
  font-weight: 800;
}
.upload-text {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 600;
}
.upload-tip {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}
</style>
