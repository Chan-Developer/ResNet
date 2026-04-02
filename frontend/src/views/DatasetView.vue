<template>
  <div class="dataset-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-icon">库</div>
      <div>
        <h2>数据集浏览</h2>
        <p class="header-desc">探索 38 种农作物病害类别，共计数万张样本图片</p>
      </div>
    </div>

    <!-- 类别网格 -->
    <div v-if="!selectedCategory">
      <div class="search-bar">
        <span class="search-icon">搜</span>
        <input v-model="searchText" placeholder="搜索类别名称..." class="search-input" />
      </div>
      <div class="category-grid">
        <CategoryCard
          v-for="cat in filteredCategories"
          :key="cat.name"
          :category="cat"
          @click="selectCategory(cat)"
        />
      </div>
      <div v-if="filteredCategories.length === 0" class="empty-state">
        <div class="empty-icon">·</div>
        <p>没有找到匹配的类别</p>
      </div>
    </div>

    <!-- 类别内图片 -->
    <div v-else>
      <div class="back-header">
        <button class="back-btn" @click="selectedCategory = null">
          <span>←</span>
          <span>返回类别列表</span>
        </button>
        <div class="category-title">
          <h3>{{ selectedCategory.display_name }}</h3>
          <span class="count-badge">{{ selectedCategory.count }} 张</span>
        </div>
      </div>

      <div class="image-grid" v-loading="imgLoading">
        <div v-for="img in images" :key="img.filename" class="image-item">
          <el-image :src="img.url" fit="cover" :preview-src-list="images.map((i: any) => i.url)" lazy />
        </div>
      </div>

      <div v-if="imgTotal > 0" class="pagination-wrap">
        <el-pagination
          layout="prev, pager, next"
          :total="imgTotal"
          :page-size="imgPageSize"
          v-model:current-page="imgPage"
          @current-change="fetchImages"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import CategoryCard from '../components/CategoryCard.vue'
import { getCategories, getCategoryImages } from '../api/dataset'

const categories = ref<any[]>([])
const selectedCategory = ref<any>(null)
const searchText = ref('')

const images = ref<any[]>([])
const imgLoading = ref(false)
const imgTotal = ref(0)
const imgPage = ref(1)
const imgPageSize = 24

const filteredCategories = computed(() => {
  if (!searchText.value) return categories.value
  const kw = searchText.value.toLowerCase()
  return categories.value.filter(
    (c: any) =>
      c.name.toLowerCase().includes(kw) ||
      c.display_name.toLowerCase().includes(kw)
  )
})

onMounted(async () => {
  const res: any = await getCategories()
  categories.value = res.data
})

function selectCategory(cat: any) {
  selectedCategory.value = cat
  imgPage.value = 1
  fetchImages()
}

async function fetchImages() {
  imgLoading.value = true
  try {
    const res: any = await getCategoryImages(selectedCategory.value.name, imgPage.value, imgPageSize)
    images.value = res.data.items
    imgTotal.value = res.data.total
  } finally {
    imgLoading.value = false
  }
}
</script>

<style scoped>
.dataset-page {
  max-width: 1050px;
  margin: 0 auto;
  padding: 32px 24px;
}

/* Header */
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}
.header-icon {
  font-size: 13px;
  font-weight: 800;
  color: var(--pink-deep);
  background: linear-gradient(135deg, var(--green-light), var(--peach-light));
  width: 64px;
  height: 64px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--shadow-soft);
}
.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
}
.header-desc {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 600;
}

/* Search */
.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--card-bg);
  backdrop-filter: var(--glass-blur);
  border: 1.5px solid #e8d8df;
  border-radius: var(--radius-sm);
  padding: 0 16px;
  margin-bottom: 20px;
  transition: border-color 0.2s;
}
.search-bar:focus-within {
  border-color: var(--pink);
}
.search-icon {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--lavender-light);
  border-radius: 8px;
  padding: 4px 6px;
  font-weight: 700;
}
.search-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 12px 0;
  font-size: 14px;
  color: var(--text-primary);
  outline: none;
  font-family: inherit;
}
.search-input::placeholder {
  color: var(--text-muted);
}

/* Category Grid */
.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
}

/* Back header */
.back-header {
  margin-bottom: 20px;
}
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1.5px solid #e8d8df;
  border-radius: var(--radius-sm);
  background: rgba(255,255,255,0.6);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  margin-bottom: 12px;
}
.back-btn:hover {
  border-color: var(--pink);
  background: var(--pink-light);
  color: var(--pink-deep);
}
.category-title {
  display: flex;
  align-items: center;
  gap: 12px;
}
.category-title h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: var(--text-primary);
}
.count-badge {
  background: linear-gradient(135deg, var(--green-light), var(--sky-light));
  color: var(--green-deep);
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
}

/* Image Grid */
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
  min-height: 200px;
}
.image-item {
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 2px solid transparent;
  transition: border-color 0.2s, transform 0.2s;
}
.image-item:hover {
  border-color: var(--pink);
  transform: translateY(-2px);
}
.image-item .el-image {
  width: 100%;
  height: 140px;
  display: block;
}

/* Pagination */
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

/* Empty */
.empty-state {
  text-align: center;
  padding: 40px 20px;
}
.empty-icon { font-size: 48px; margin-bottom: 8px; }
.empty-state p {
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 600;
}

@media (max-width: 720px) {
  .image-item .el-image {
    height: 120px;
  }
  .category-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
}
</style>
