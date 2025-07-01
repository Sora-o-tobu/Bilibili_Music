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
                <div>
                  <el-radio-group v-model="playbackMode" size="mini">
                    <el-radio-button label="sequence">顺序播放</el-radio-button>
                    <el-radio-button label="random">随机播放</el-radio-button>
                  </el-radio-group>
                  <el-button class="button" type="text" @click="refreshMusicLibrary" style="margin-left: 10px;"><i class="el-icon-refresh"></i> 刷新</el-button>
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
                    <el-button size="small" type="primary" @click="playMusic(scope.row)" round>
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
});
const playbackMode = ref('sequence'); // 'sequence' or 'random'

function isPlaying(music) {
  return currentlyPlaying.filePath === music.file_path && !currentlyPlaying.paused;
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

async function refreshMusicLibrary() {
  const result = await window.pywebview.api.get_music_library();
  if (Array.isArray(result)) {
      musicLibrary.value = result;
  } else {
      console.error("get_music_library did not return an array:", result);
      musicLibrary.value = [];
  }
}

// 将函数暴露给全局 window 对象
window.refreshMusicLibrary = refreshMusicLibrary;

async function playMusic(music) {
  const isCurrentTrack = currentlyPlaying.filePath === music.file_path;

  // If it's the current track, toggle play/pause
  if (isCurrentTrack && currentlyPlaying.audio) {
    if (currentlyPlaying.audio.paused) {
      currentlyPlaying.audio.play();
      currentlyPlaying.paused = false;
    } else {
      currentlyPlaying.audio.pause();
      currentlyPlaying.paused = true;
    }
    return;
  }

  // If another track is playing, stop it
  if (currentlyPlaying.audio) {
    currentlyPlaying.audio.pause();
    currentlyPlaying.audio.src = ''; // Release the audio source
  }
  
  // Get the URL for the audio file from the backend
  const url = await window.pywebview.api.get_media_url(music.file_path);
  if (!url) {
      ElMessage.error("无法获取音频文件URL");
      return;
  }

  const audio = new Audio(url);
  
  audio.oncanplay = () => {
    audio.play();
    currentlyPlaying.paused = false;
  };

  audio.onended = () => {
    playNext();
  };
  
  audio.onerror = (e) => {
    ElMessage.error('播放失败，请检查控制台日志');
    console.error("Audio Error:", e);
    currentlyPlaying.audio = null;
    currentlyPlaying.filePath = null;
    currentlyPlaying.paused = true;
  };

  currentlyPlaying.audio = audio;
  currentlyPlaying.filePath = music.file_path;
}

function playNext() {
  if (musicLibrary.value.length === 0) return;

  const currentIndex = musicLibrary.value.findIndex(m => m.file_path === currentlyPlaying.filePath);
  let nextIndex;

  if (playbackMode.value === 'random') {
    nextIndex = Math.floor(Math.random() * musicLibrary.value.length);
  } else { // sequence
    nextIndex = (currentIndex + 1) % musicLibrary.value.length;
  }
  
  if (nextIndex >= 0 && nextIndex < musicLibrary.value.length) {
    playMusic(musicLibrary.value[nextIndex]);
  }
}

async function deleteMusic(music) {
  try {
    // Stop playback if the deleted music is currently playing
    if (currentlyPlaying.filePath === music.file_path && currentlyPlaying.audio) {
      currentlyPlaying.audio.pause();
      currentlyPlaying.audio = null;
      currentlyPlaying.filePath = null;
      currentlyPlaying.paused = true;
    }
    await window.pywebview.api.delete_music(music.file_path);
    refreshMusicLibrary();
  } catch (error) {
    ElMessage.error('删除失败，请检查控制台日志');
    console.error("Delete Music Error:", error);
  }
}

onMounted(() => {
  checkLogin();
  // 启动时不再需要此调用，由后端触发
});

</script>

<style>
body {
  margin: 0;
  font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
}

.header {
  background-color: #ffffff;
  color: #333;
  line-height: 60px;
  border-bottom: 1px solid #e6e6e6;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);
}

.header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 500;
}

.el-main {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 500;
}

.box-card {
  border-radius: 12px;
}

.video-info {
  margin-top: 20px;
  padding: 15px;
  background-color: #fafafa;
  border-radius: 8px;
}

.video-info p {
  margin: 8px 0;
}

.image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  color: #c0c4cc;
  font-size: 30px;
  border-radius: 8px;
}

.el-button i {
  margin-right: 5px;
}
</style>
