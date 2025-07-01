<!-- App.vue，基本由 AI 生成 -->
<template>
  <el-container style="height: 100vh; background-color: #f4f4f5;">
    <el-header class="header">
      <el-row align="middle" justify="space-between">
        <el-col :span="12">
          <h1><i class="el-icon-headset"></i> Bilibili</h1>
        </el-col>
        <el-col :span="12" style="text-align: right;">
          <el-button @click="checkLogin" type="primary" round>
            <i class="el-icon-user"></i> 检查登录状态
          </el-button>
        </el-col>
      </el-row>
    </el-header>
    <el-main>
      <el-row :gutter="24">
        <el-col :span="8">
          <el-card class="box-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span><i class="el-icon-download"></i> 下载新音频</span>
              </div>
            </template>
            <el-input v-model="videoUrl" placeholder="输入视频URL或BV号" clearable @keyup.enter="loadVideoInfo"></el-input>
            <el-button @click="loadVideoInfo" type="primary" style="margin-top: 15px; width: 100%;">加载信息</el-button>
            <div v-if="videoInfo" class="video-info">
              <p><strong>标题:</strong> {{ videoInfo.title }}</p>
              <el-button @click="downloadAudio" type="success" style="margin-top: 10px; width: 100%;" round>
                <i class="el-icon-bottom"></i> 下载音频
              </el-button>
            </div>
          </el-card>
        </el-col>
        <el-col :span="16">
          <el-card class="box-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span><i class="el-icon-notebook-2"></i> 音乐库</span>
                <div class="header-controls">
                  <el-button class="button" type="text" @click="showFavoritesDialog"><i class="el-icon-star-off"></i> 查看收藏夹</el-button>
                  <el-radio-group v-model="playbackMode" size="mini">
                    <el-radio-button label="sequence">顺序播放</el-radio-button>
                    <el-radio-button label="random">随机播放</el-radio-button>
                  </el-radio-group>
                  <div class="volume-slider">
                    <i class="el-icon-volume-up"></i>
                    <el-slider v-model="volume" @input="updateVolume" size="mini" style="width: 120px; margin-left: 8px;"></el-slider>
                  </div>
                  <el-button class="button" type="text" @click="refreshMusicLibrary"><i class="el-icon-refresh"></i> 刷新</el-button>
                </div>
              </div>
            </template>
            <el-table :data="musicLibrary" style="width: 100%" height="calc(100vh - 260px)">
              <el-table-column label="封面" width="100">
                <template #default="scope">
                  <el-image
                    style="width: 80px; height: 80px; border-radius: 8px;"
                    :src="scope.row.cover_url"
                    fit="cover"
                  >
                    <template #error>
                      <div class="image-slot">
                        <i class="el-icon-picture-outline"></i>
                      </div>
                    </template>
                  </el-image>
                </template>
              </el-table-column>
              <el-table-column prop="title" label="标题" show-overflow-tooltip></el-table-column>
              <el-table-column label="操作" width="200">
                <template #default="scope">
                  <el-button-group>
                    <el-button size="small" :type="isPlaying(scope.row) ? 'success' : 'primary'" @click="playMusic(scope.row)" round>
                      <i :class="isPlaying(scope.row) ? 'el-icon-video-pause' : 'el-icon-video-play'"></i> 
                      {{ isPlaying(scope.row) ? '暂停' : '播放' }}
                    </el-button>
                    <el-button size="small" type="danger" @click="deleteMusic(scope.row)" round><i class="el-icon-delete"></i> 删除</el-button>
                  </el-button-group>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </el-main>

    <el-dialog v-model="favoritesDialogVisible" title="我的收藏夹" width="80%" top="5vh">
      <el-button @click="refreshFavorites" :loading="favoritesLoading" icon="el-icon-refresh" style="margin-bottom: 15px;">刷新列表</el-button>
      <el-collapse v-model="activeFavoriteNames" class="favorites-collapse">
        <el-collapse-item v-for="folder in favoriteFolders" :key="folder.id" :name="folder.id">
            <template #title>
                <div class="folder-title-wrapper">
                    <span class="folder-title">{{ folder.title }}</span>
                    <el-tag class="folder-count" size="small">{{ folder.media_count }} 个内容</el-tag>
                    <div class="folder-actions">
                        <el-button 
                            size="small" 
                            @click.stop="downloadAllFromFolder(folder)"
                            :loading="downloadingState.folders[folder.id]">
                            <i class="el-icon-download"></i> 一键下载全部
                        </el-button>
                    </div>
                </div>
            </template>
            <el-table :data="folder.videos" height="400px" style="width: 100%;">
                <el-table-column prop="title" label="标题" show-overflow-tooltip></el-table-column>
                <el-table-column label="操作" width="120">
                    <template #default="scope">
                        <el-button 
                            size="small" 
                            type="primary" 
                            @click="downloadFavoriteVideo(scope.row)"
                            :loading="downloadingState.videos[scope.row.bvid]">
                            下载
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-collapse-item>
      </el-collapse>
    </el-dialog>

    <div v-if="currentlyPlaying.filePath" class="now-playing-bar">
      <div class="song-info">
        <span class="song-title" :title="currentlyPlaying.title">正在播放: {{ currentlyPlaying.title }}</span>
      </div>
      <el-progress 
        :percentage="currentProgress" 
        :show-text="false" 
        color="#409eff"
      ></el-progress>
    </div>

  </el-container>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';

const videoUrl = ref('');
const videoInfo = ref(null);
const musicLibrary = ref([]);
const currentlyPlaying = reactive({
  audio: null,
  filePath: null,
  paused: true,
  title: '',
});
const currentProgress = ref(0);
const playbackMode = ref('sequence'); // 'sequence' or 'random'
const volume = ref(80); // Volume from 0 to 100
const favoriteFolders = ref([]);
const favoritesLoading = ref(false);
const favoritesDialogVisible = ref(false);
const activeFavoriteFolder = ref(null);
const activeFavoriteNames = ref([]);
const downloadingState = reactive({ videos: {}, folders: {} });

async function refreshMusicLibrary() {
  try {
    const result = await window.pywebview.api.get_music_library();
    if (Array.isArray(result)) {
        musicLibrary.value = result;
    } else {
        console.error("get_music_library did not return an array:", result);
        musicLibrary.value = [];
    }
  } catch (e) {
    console.error("Failed to refresh music library:", e);
    ElMessage.error("加载音乐库失败");
  }
}

onMounted(() => {
  // Expose a function for Python to call when the webview is ready.
  window.onPywebviewReady = () => {
    console.log("pywebview is ready, loading music library.");
    refreshMusicLibrary();
  };
  // Expose the refresh function for manual calls from the UI.
  window.refreshMusicLibrary = refreshMusicLibrary;
});

function updateProgress() {
  if (!currentlyPlaying.audio || currentlyPlaying.audio.duration === 0) {
    currentProgress.value = 0;
    return;
  }
  const progress = (currentlyPlaying.audio.currentTime / currentlyPlaying.audio.duration) * 100;
  currentProgress.value = progress || 0;
}

function isPlaying(music) {
  return currentlyPlaying.filePath === music.file_path && !currentlyPlaying.paused;
}

function updateVolume(newVolume) {
  if (currentlyPlaying.audio) {
    currentlyPlaying.audio.volume = newVolume / 100;
  }
}

async function playMusic(music) {
  if (currentlyPlaying.filePath === music.file_path) {
    if (currentlyPlaying.audio && !currentlyPlaying.paused) {
      currentlyPlaying.audio.pause();
      currentlyPlaying.paused = true;
    } else if (currentlyPlaying.audio) {
      currentlyPlaying.audio.play();
      currentlyPlaying.paused = false;
    }
  } else {
    if (currentlyPlaying.audio) {
      currentlyPlaying.audio.pause();
    }

    try {
      const audioUrl = await window.pywebview.api.get_audio_file_url(music.file_path);
      if (!audioUrl) {
        ElMessage.error('获取音频URL失败');
        return;
      }

      const audio = new Audio(audioUrl);
      audio.volume = volume.value / 100;
      audio.play();

      currentProgress.value = 0;
      currentlyPlaying.audio = audio;
      currentlyPlaying.filePath = music.file_path;
      currentlyPlaying.title = music.title;
      currentlyPlaying.paused = false;

      audio.addEventListener('timeupdate', () => {
        if (currentlyPlaying.audio && currentlyPlaying.audio.duration) {
          currentProgress.value = (currentlyPlaying.audio.currentTime / currentlyPlaying.audio.duration) * 100;
        }
      });

      audio.onended = () => {
        currentProgress.value = 0;
        playNext();
      };
    } catch (e) {
      console.error("播放音乐失败:", e);
      ElMessage.error('播放音乐失败');
    }
  }
}

function playNext() {
    const currentIndex = musicLibrary.value.findIndex(m => m.file_path === currentlyPlaying.filePath);
    if (currentIndex === -1 || musicLibrary.value.length === 0) return;

    let nextIndex;
    if (playbackMode.value === 'random') {
        if (musicLibrary.value.length > 1) {
            do {
                nextIndex = Math.floor(Math.random() * musicLibrary.value.length);
            } while (nextIndex === currentIndex);
        } else {
            nextIndex = 0;
        }
    } else { // sequence
        nextIndex = (currentIndex + 1) % musicLibrary.value.length;
    }
    
    if (musicLibrary.value[nextIndex]) {
        playMusic(musicLibrary.value[nextIndex]);
    }
}

async function deleteMusic(music) {
  try {
    await ElMessageBox.confirm(`确定要删除歌曲 "${music.title}" 吗？文件将从磁盘删除。`, '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    });
    
    const result = await window.pywebview.api.delete_music(music.file_path);
    if (result.status === 'ok') {
      ElMessage.success(result.message || '删除成功');
      if (currentlyPlaying.filePath === music.file_path) {
        if (currentlyPlaying.audio) {
          currentlyPlaying.audio.pause();
        }
        currentlyPlaying.audio = null;
        currentlyPlaying.filePath = null;
        currentlyPlaying.paused = true;
        currentlyPlaying.title = '';
        currentProgress.value = 0;
      }
      await refreshMusicLibrary();
    } else {
      ElMessage.error(result.message || '删除失败');
    }
  } catch (e) {
    if (e !== 'cancel') {
        console.error("Delete music error:", e);
        ElMessage.error('删除操作失败');
    } else {
      ElMessage.info('已取消删除');
    }
  }
}

async function checkLogin() {
  const result = await window.pywebview.api.ensure_login();
  if (result.status === 'qrcode') {
    ElMessageBox.alert(`<img src="data:image/png;base64,${result.qrcode}" width="200"/>`, '请扫描二维码登录', {
      dangerouslyUseHTMLString: true,
      showConfirmButton: false,
      center: true,
    });
    pollLoginStatus(result.qrcode_key);
  } else {
    ElMessage.success(result.message);
  }
}

async function pollLoginStatus(qrcode_key) {
  const interval = setInterval(async () => {
    const result = await window.pywebview.api.poll_login_status(qrcode_key);
    if (result.status === 'ok') {
      clearInterval(interval);
      ElMessageBox.close();
      ElMessage.success(result.message);
    } else if (result.status === 'error') {
      clearInterval(interval);
      ElMessageBox.close();
      ElMessage.error(result.message);
    }
  }, 2000);
}

async function loadVideoInfo() {
  const result = await window.pywebview.api.load_video_info(videoUrl.value);
  if (result.status === 'ok') {
    videoInfo.value = result.video;
  } else {
    ElMessage.error(result.message);
  }
}

async function downloadAudio() {
  const result = await window.pywebview.api.download_audio(videoInfo.value);
  if (result.status === 'ok') {
    ElMessage.success(result.message);
    refreshMusicLibrary();
  } else {
    ElMessage.error(result.message);
  }
}

async function showFavoritesDialog() {
  favoritesDialogVisible.value = true;
  if (favoriteFolders.value.length === 0) {
      await loadFavorites(false); // Load from cache first or fetch if empty
  }
  // 默认不展开任何面板
  activeFavoriteNames.value = []; 
}

async function refreshFavorites() {
  await loadFavorites(true); // Force refresh from API
}

async function loadFavorites(forceRefresh) {
  favoritesLoading.value = true;
  try {
    const result = await window.pywebview.api.get_favorites(forceRefresh);
    if (result.status === 'ok') {
      favoriteFolders.value = result.favorites;
    } else {
      ElMessage.error(result.message || '加载收藏夹失败');
    }
  } catch (e) {
    ElMessage.error('加载收藏夹时出错: ' + e.message);
    console.error(e);
  } finally {
    favoritesLoading.value = false;
  }
}

async function downloadFavoriteVideo(video) {
  if (downloadingState.videos[video.bvid]) return; // 防止重复点击
  downloadingState.videos[video.bvid] = true;
  ElMessage.info(`开始下载: ${video.title}`);
  try {
    const result = await window.pywebview.api.download_audio(video);
    if (result.status === 'ok') {
      ElMessage.success(`${video.title} 下载完成`);
      refreshMusicLibrary(); // Refresh the main library
    } else {
      ElMessage.error(result.message || `${video.title} 下载失败`);
    }
  } catch (e) {
      ElMessage.error(`下载 ${video.title} 时出错: ${e.message}`);
  } finally {
      downloadingState.videos[video.bvid] = false;
  }
}

async function downloadAllFromFolder(folder) {
    if (downloadingState.folders[folder.id]) return;
    downloadingState.folders[folder.id] = true;
    ElMessage.info(`开始下载收藏夹「${folder.title}」中的所有内容...`);

    let successCount = 0;
    let failCount = 0;

    for (const video of folder.videos) {
        // 使用已有的下载函数，但避免重复的状态管理
        if (downloadingState.videos[video.bvid]) continue;
        downloadingState.videos[video.bvid] = true;
        try {
            const result = await window.pywebview.api.download_audio(video);
            if (result.status === 'ok') {
                successCount++;
                ElMessage.success(`视频 ${video.title} 下载完成`);
            } else {
                failCount++;
                ElMessage.error(`视频 ${video.title} 下载失败: ${result.message}`);
            }
        } catch (e) {
            failCount++;
            ElMessage.error(`下载视频 ${video.title} 时出错: ${e.message}`);
        } finally {
            downloadingState.videos[video.bvid] = false;
        }
    }

    downloadingState.folders[folder.id] = false;

    if (successCount > 0) {
        ElMessage.success(`收藏夹「${folder.title}」中的 ${successCount} 个视频下载完成`);
    }
    if (failCount > 0) {
        ElMessage.warning(`收藏夹「${folder.title}」中的 ${failCount} 个视频下载失败`);
    }
}

</script>

<style>
.header {
  background-color: #409eff;
  color: white;
  padding: 0 20px;
  font-size: 18px;
  font-weight: bold;
}

.box-card {
  border-radius: 8px;
  overflow: hidden;
}

.card-header {
  background-color: #f5f7fa;
  padding: 10px 15px;
  font-size: 16px;
  font-weight: 500;
  border-bottom: 1px solid #e4e7ed;
}

.el-table {
  border-radius: 8px;
  overflow: hidden;
}

.el-table th, .el-table td {
  padding: 12px 15px;
  vertical-align: middle;
}

.el-table th {
  background-color: #f5f7fa;
  color: #333;
  font-weight: 600;
}

.el-table td {
  background-color: #fff;
  color: #666;
}

.el-table tr:hover td {
  background-color: #f1f9ff;
}

.volume-slider {
  display: flex;
  align-items: center;
}

.image-slot {
  width: 100px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  border-radius: 4px;
  color: #bbb;
}

.el-dialog {
  border-radius: 8px;
}

.el-collapse-item__header {
    display: flex;
    align-items: center;
    width: 100%;
}

.favorites-collapse {
  margin-top: 10px;
}

.folder-title-wrapper {
    display: grid;
    grid-template-columns: 1fr auto auto;
    gap: 10px;
    align-items: center;
    width: 100%;
    overflow: hidden;
    padding: 10px 15px;
    box-sizing: border-box;
}

.folder-title {
    font-size: 16px;
    font-weight: bold;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.folder-count {
    white-space: nowrap;
}

.folder-actions {
    justify-self: end;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.el-collapse-item__header {
  font-size: 16px;
  font-weight: 500;
  padding: 0; /* Remove padding from header */
}

.el-collapse-item__content {
  padding: 0 15px 15px;
}

.now-playing-bar {
  position: fixed;
  bottom: 10px;
  left: 24px; /* Corresponds to el-row gutter */
  width: 350px;
  background-color: rgba(255, 255, 255, 0.95);
  border: 1px solid #e9e9eb;
  border-radius: 8px;
  padding: 10px 15px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  z-index: 2000; /* Make sure it's on top */
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: opacity 0.3s, transform 0.3s;
  backdrop-filter: blur(5px);
}

.song-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.song-title {
  font-weight: 500;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
</style>
