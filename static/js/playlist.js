// 播放列表JavaScript

let currentPlaylist = null;
let allPlaylists = [];
let allVideos = [];
let userSession = 'default';

// 获取用户会话ID
function getUserSession() {
    let session = localStorage.getItem('dplayer_session');
    if (!session) {
        session = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('dplayer_session', session);
    }
    userSession = session;
    return session;
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    getUserSession();
    loadPlaylists();
    loadVideos();
    setupEventListeners();
});

// 设置事件监听器
function setupEventListeners() {
    document.getElementById('playlist-form').addEventListener('submit', handlePlaylistSubmit);
}

// 加载播放列表
async function loadPlaylists() {
    try {
        const response = await fetch(`/api/playlist/?user_session=${userSession}`);
        const data = await response.json();

        if (data.success) {
            allPlaylists = data.playlists;
            renderPlaylists(allPlaylists);
        } else {
            console.error('加载播放列表失败:', data.error);
        }
    } catch (error) {
        console.error('加载播放列表失败:', error);
    }
}

// 渲染播放列表
function renderPlaylists(playlists) {
    const container = document.getElementById('playlist-list');

    if (playlists.length === 0) {
        container.innerHTML = '<p class="empty-message">暂无播放列表，点击"新建播放列表"创建一个吧！</p>';
        return;
    }

    container.innerHTML = playlists.map(playlist => `
        <div class="playlist-card" onclick="openPlaylist(${playlist.id})">
            <div class="playlist-thumbnail">
                ${playlist.thumbnail ? `<img src="${playlist.thumbnail}" alt="${playlist.name}">` : '📋'}
            </div>
            <div class="playlist-name">${playlist.name}</div>
            <div class="playlist-description">${playlist.description || '暂无描述'}</div>
            <div class="playlist-meta">
                <span>📹 ${playlist.video_count}个视频</span>
                <span>⏱ ${formatDuration(playlist.total_duration)}</span>
            </div>
        </div>
    `).join('');
}

// 打开播放列表详情
function openPlaylist(playlistId) {
    const playlist = allPlaylists.find(p => p.id === playlistId);
    if (!playlist) return;

    currentPlaylist = playlist;

    document.getElementById('playlist-list').classList.add('hidden');
    document.getElementById('playlist-detail').classList.remove('hidden');

    document.getElementById('playlist-name').textContent = playlist.name;
    document.getElementById('playlist-description').textContent = playlist.description || '暂无描述';
    document.getElementById('video-count').textContent = playlist.video_count;
    document.getElementById('total-duration').textContent = formatDuration(playlist.total_duration);
    document.getElementById('play-count').textContent = playlist.play_count;
    document.getElementById('repeat-mode').value = playlist.repeat_mode || 'none';

    renderPlaylistItems(playlist.items);
}

// 渲染播放列表项
function renderPlaylistItems(items) {
    const container = document.getElementById('playlist-items');

    if (!items || items.length === 0) {
        container.innerHTML = '<p class="empty-message">播放列表为空，点击"添加视频"添加视频吧！</p>';
        return;
    }

    container.innerHTML = items.map((item, index) => `
        <div class="playlist-item ${item.video_id === currentPlaylist.current_video_id ? 'current' : ''}">
            <div class="playlist-item-number">${index + 1}</div>
            ${item.video && item.video.thumbnail ? `
                <div class="playlist-item-thumbnail">
                    <img src="${item.video.thumbnail}" alt="${item.video.title}">
                </div>
            ` : ''}
            <div class="playlist-item-info">
                <div class="playlist-item-title">${item.video ? item.video.title : '未知视频'}</div>
                <div class="playlist-item-duration">
                    ${item.video ? formatDuration(item.video.duration) : ''}
                </div>
            </div>
            <div class="playlist-item-actions">
                <button class="btn btn-primary" onclick="playVideo(${item.video_id})">▶</button>
                <button class="btn btn-danger" onclick="removeFromPlaylist(${item.id})">✕</button>
            </div>
        </div>
    `).join('');
}

// 关闭播放列表详情
function closePlaylistDetail() {
    document.getElementById('playlist-list').classList.remove('hidden');
    document.getElementById('playlist-detail').classList.add('hidden');
    currentPlaylist = null;
}

// 显示创建播放列表模态框
function showCreatePlaylistModal() {
    document.getElementById('modal-title').textContent = '新建播放列表';
    document.getElementById('playlist-id').value = '';
    document.getElementById('playlist-name-input').value = '';
    document.getElementById('playlist-description-input').value = '';
    document.getElementById('playlist-public').checked = false;
    document.getElementById('video-select').value = '';
    document.getElementById('playlist-modal').classList.add('show');
}

// 显示编辑播放列表模态框
function showEditPlaylistModal() {
    if (!currentPlaylist) return;

    document.getElementById('modal-title').textContent = '编辑播放列表';
    document.getElementById('playlist-id').value = currentPlaylist.id;
    document.getElementById('playlist-name-input').value = currentPlaylist.name;
    document.getElementById('playlist-description-input').value = currentPlaylist.description || '';
    document.getElementById('playlist-public').checked = currentPlaylist.is_public;

    // 选择已添加的视频
    const selectedVideos = currentPlaylist.items.map(item => item.video_id);
    const select = document.getElementById('video-select');
    Array.from(select.options).forEach(option => {
        option.selected = selectedVideos.includes(parseInt(option.value));
    });

    document.getElementById('playlist-modal').classList.add('show');
}

// 关闭播放列表模态框
function closePlaylistModal() {
    document.getElementById('playlist-modal').classList.remove('show');
}

// 处理播放列表表单提交
async function handlePlaylistSubmit(event) {
    event.preventDefault();

    const playlistId = document.getElementById('playlist-id').value;
    const name = document.getElementById('playlist-name-input').value;
    const description = document.getElementById('playlist-description-input').value;
    const isPublic = document.getElementById('playlist-public').checked;
    const selectedVideos = Array.from(document.getElementById('video-select').selectedOptions).map(opt => parseInt(opt.value));

    const data = {
        name,
        description,
        user_session: userSession,
        is_public: isPublic,
        video_ids: selectedVideos
    };

    try {
        const url = playlistId ? `/api/playlist/${playlistId}` : '/api/playlist/';
        const method = playlistId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            closePlaylistModal();
            await loadPlaylists();

            if (currentPlaylist && playlistId) {
                openPlaylist(parseInt(playlistId));
            }

            alert('保存成功！');
        } else {
            alert('保存失败: ' + result.error);
        }
    } catch (error) {
        console.error('保存播放列表失败:', error);
        alert('保存失败: ' + error.message);
    }
}

// 加载视频列表
async function loadVideos() {
    try {
        const response = await fetch('/api/videos/');
        const data = await response.json();

        if (data.success) {
            allVideos = data.videos;
            updateVideoSelects();
        }
    } catch (error) {
        console.error('加载视频列表失败:', error);
    }
}

// 更新视频选择框
function updateVideoSelects() {
    const options = allVideos.map(video => `
        <option value="${video.id}">${video.title}</option>
    `).join('');

    document.getElementById('video-select').innerHTML = options || '<option value="">暂无视频</option>';
    document.getElementById('add-video-select').innerHTML = options || '<option value="">暂无视频</option>';
}

// 播放播放列表
async function playPlaylist() {
    if (!currentPlaylist) return;

    try {
        const response = await fetch(`/api/playlist/${currentPlaylist.id}/play`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            const firstVideo = result.playlist.items[0];
            if (firstVideo && firstVideo.video) {
                playVideo(firstVideo.video_id);
            }
        }
    } catch (error) {
        console.error('播放播放列表失败:', error);
    }
}

// 播放视频
function playVideo(videoId) {
    const video = allVideos.find(v => v.id === videoId);
    if (video) {
        window.location.href = `/video/${videoId}`;
    }
}

// 下一首
async function playNext() {
    if (!currentPlaylist) return;

    try {
        const response = await fetch(`/api/playlist/${currentPlaylist.id}/next`);
        const result = await response.json();

        if (result.success && result.video) {
            if (result.video) {
                playVideo(result.video.id);
                // 刷新播放列表以更新当前视频
                openPlaylist(currentPlaylist.id);
            } else {
                alert('播放列表已结束');
            }
        }
    } catch (error) {
        console.error('播放下一首失败:', error);
    }
}

// 上一首
async function playPrevious() {
    if (!currentPlaylist) return;

    try {
        const response = await fetch(`/api/playlist/${currentPlaylist.id}/previous`);
        const result = await response.json();

        if (result.success && result.video) {
            playVideo(result.video.id);
            openPlaylist(currentPlaylist.id);
        } else {
            alert('已是第一个视频');
        }
    } catch (error) {
        console.error('播放上一首失败:', error);
    }
}

// 随机播放列表
async function shufflePlaylist() {
    if (!currentPlaylist) return;

    try {
        const response = await fetch(`/api/playlist/${currentPlaylist.id}/shuffle`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            alert('已随机排序播放列表');
            openPlaylist(currentPlaylist.id);
        }
    } catch (error) {
        console.error('随机播放列表失败:', error);
    }
}

// 改变重复模式
async function changeRepeatMode() {
    if (!currentPlaylist) return;

    const repeatMode = document.getElementById('repeat-mode').value;

    try {
        const response = await fetch(`/api/playlist/${currentPlaylist.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ repeat_mode: repeatMode })
        });

        const result = await response.json();

        if (result.success) {
            currentPlaylist = result.playlist;
            alert('重复模式已更新');
        }
    } catch (error) {
        console.error('更新重复模式失败:', error);
    }
}

// 删除播放列表
async function deletePlaylist() {
    if (!currentPlaylist) return;

    if (!confirm(`确定要删除播放列表"${currentPlaylist.name}"吗？`)) {
        return;
    }

    try {
        const response = await fetch(`/api/playlist/${currentPlaylist.id}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            alert('播放列表已删除');
            closePlaylistDetail();
            loadPlaylists();
        } else {
            alert('删除失败: ' + result.error);
        }
    } catch (error) {
        console.error('删除播放列表失败:', error);
        alert('删除失败: ' + error.message);
    }
}

// 从播放列表移除视频
async function removeFromPlaylist(itemId) {
    if (!currentPlaylist) return;

    if (!confirm('确定要从播放列表移除这个视频吗？')) {
        return;
    }

    try {
        const response = await fetch(`/api/playlist/${currentPlaylist.id}/items/${itemId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            openPlaylist(currentPlaylist.id);
        } else {
            alert('移除失败: ' + result.error);
        }
    } catch (error) {
        console.error('从播放列表移除视频失败:', error);
        alert('移除失败: ' + error.message);
    }
}

// 格式化时长
function formatDuration(seconds) {
    if (!seconds) return '0:00';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}
