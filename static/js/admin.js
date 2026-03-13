// ========== 状态管理 ==========

let autoRefreshInterval = null;

function showAppAlert(message, type) {
    const alert = document.getElementById('appAlert');
    alert.className = `alert ${type} show`;
    alert.textContent = message;

    setTimeout(() => {
        alert.classList.remove('show');
    }, 5000);
}

function showVideoAlert(message, type) {
    const alert = document.getElementById('videoAlert');
    alert.className = `alert ${type} show`;
    alert.textContent = message;

    setTimeout(() => {
        alert.classList.remove('show');
    }, 5000);
}

function showTagAlert(message, type) {
    const alert = document.getElementById('tagAlert');
    alert.className = `alert ${type} show`;
    alert.textContent = message;

    setTimeout(() => {
        alert.classList.remove('show');
    }, 5000);
}

function showDbAlert(message, type) {
    const alert = document.getElementById('dbAlert');
    alert.className = `alert ${type} show`;
    alert.textContent = message;

    setTimeout(() => {
        alert.classList.remove('show');
    }, 5000);
}

function updateRefreshTime() {
    const now = new Date();
    document.getElementById('refreshTime').textContent = now.toLocaleString('zh-CN');
}

// ========== 标签页切换 ==========

function switchTab(tabName) {
    // 隐藏所有标签页
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });

    // 移除所有按钮的 active 类
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // 显示选中的标签页
    document.getElementById(`tab-${tabName}`).classList.add('active');

    // 激活对应的按钮
    event.target.classList.add('active');

    // 刷新数据
    if (tabName === 'app') {
        refreshStatus();
    } else if (tabName === 'database') {
        refreshDbStats();
    }
}

// ========== 按钮状态管理 ==========

function setButtonLoading(btn, loading) {
    if (loading) {
        btn.classList.add('loading');
        btn.disabled = true;
    } else {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

function setAllButtonsLoading(loading) {
    document.querySelectorAll('.btn').forEach(btn => {
        if (!btn.disabled) {
            setButtonLoading(btn, loading);
        }
    });
}

// ========== API 调用 ==========

async function apiCall(url, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {}
        };

        if (data) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('API调用失败:', error);
        return { success: false, message: '网络请求失败' };
    }
}

// ========== 应用控制 ==========

async function refreshStatus() {
    const refreshBtn = document.getElementById('refreshBtn');
    setButtonLoading(refreshBtn, true);

    const result = await apiCall('/api/status');

    setButtonLoading(refreshBtn, false);

    if (result.success) {
        // 更新主应用状态
        const mainApp = result.main_app;
        const mainAppStatus = document.getElementById('mainAppStatus');
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const restartBtn = document.getElementById('restartBtn');

        if (mainApp.running) {
            mainAppStatus.className = 'status-item success';
            mainAppStatus.querySelector('.status-value').textContent = `运行中 (PID: ${mainApp.pid})`;
            startBtn.disabled = true;
            stopBtn.disabled = false;
            restartBtn.disabled = false;
        } else {
            mainAppStatus.className = 'status-item danger';
            mainAppStatus.querySelector('.status-value').textContent = mainApp.status || '未运行';
            startBtn.disabled = false;
            stopBtn.disabled = true;
            restartBtn.disabled = true;
        }

        // 更新系统状态
        const system = result.system;
        document.getElementById('systemStatus').querySelector('.status-value').textContent = `${system.cpu_percent}%`;
        document.getElementById('memoryStatus').querySelector('.status-value').textContent = `${system.memory_used.toFixed(1)}GB (${system.memory_percent}%)`;
        document.getElementById('diskStatus').querySelector('.status-value').textContent = `${system.disk_used.toFixed(1)}GB (${system.disk_percent}%)`;

        // 更新时间
        updateRefreshTime();
    } else {
        showAppAlert('获取状态失败: ' + result.message, 'error');
    }
}

async function startApp() {
    const startBtn = document.getElementById('startBtn');
    setButtonLoading(startBtn, true);

    const result = await apiCall('/api/app/start', 'POST');

    setButtonLoading(startBtn, false);

    if (result.success) {
        showAppAlert(result.message, 'success');
        setTimeout(refreshStatus, 2000);
    } else {
        showAppAlert(result.message, 'error');
    }
}

async function stopApp() {
    const stopBtn = document.getElementById('stopBtn');
    setButtonLoading(stopBtn, true);

    const result = await apiCall('/api/app/stop', 'POST');

    setButtonLoading(stopBtn, false);

    if (result.success) {
        showAppAlert(result.message, 'success');
        setTimeout(refreshStatus, 2000);
    } else {
        showAppAlert(result.message, 'error');
    }
}

async function restartApp() {
    const restartBtn = document.getElementById('restartBtn');
    setButtonLoading(restartBtn, true);

    const result = await apiCall('/api/app/restart', 'POST');

    setButtonLoading(restartBtn, false);

    if (result.success) {
        showAppAlert(result.message, 'success');
        setTimeout(refreshStatus, 5000); // 重启需要更长时间
    } else {
        showAppAlert(result.message, 'error');
    }
}

// ========== 视频管理 ==========

async function loadVideos(page = 1, perPage = 20) {
    const tableBody = document.querySelector('#videosTable tbody');
    tableBody.innerHTML = '<tr><td colspan="7" style="text-align: center;">加载中...</td></tr>';

    const result = await apiCall(`/api/videos?page=${page}&per_page=${perPage}`);

    if (result.success) {
        const videos = result.videos;
        const total = result.total;
        const pages = result.pages;

        tableBody.innerHTML = videos.map(video => `
            <tr>
                <td>${video.id}</td>
                <td>${video.title}</td>
                <td><a href="${video.url}" target="_blank">${video.url.substring(0, 50)}...</a></td>
                <td>${video.duration ? formatDuration(video.duration) : '--'}</td>
                <td>${video.priority}</td>
                <td>${video.is_downloaded ? '是' : '否'}</td>
                <td>
                    <button class="btn btn-danger" style="padding: 5px 10px; font-size: 0.8em;" onclick="deleteVideo('${video.hash}')">删除</button>
                </td>
            </tr>
        `).join('');

        // 更新分页
        updatePagination('videoPagination', page, pages, loadVideos);

        showVideoAlert(`加载了 ${videos.length} 个视频`, 'success');
    } else {
        tableBody.innerHTML = '<tr><td colspan="7" style="text-align: center;">加载失败: ' + result.message + '</td></tr>';
        showVideoAlert('加载失败: ' + result.message, 'error');
    }
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

function updatePagination(containerId, currentPage, totalPages, callback) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        if (i === currentPage) {
            btn.classList.add('active');
        }
        btn.onclick = () => callback(i);
        container.appendChild(btn);
    }
}

function showAddVideoModal() {
    document.getElementById('addVideoModal').classList.add('show');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

async function addVideo(event) {
    event.preventDefault();

    const btn = event.target.querySelector('button[type="submit"]');
    setButtonLoading(btn, true);

    const data = {
        title: document.getElementById('videoTitle').value,
        url: document.getElementById('videoUrl').value,
        thumbnail: document.getElementById('videoThumbnail').value,
        description: document.getElementById('videoDescription').value,
        priority: parseInt(document.getElementById('videoPriority').value)
    };

    const result = await apiCall('/api/video/add', 'POST', data);

    setButtonLoading(btn, false);

    if (result.success) {
        showVideoAlert(result.message, 'success');
        closeModal('addVideoModal');
        document.getElementById('addVideoForm').reset();
        loadVideos();
    } else {
        showVideoAlert(result.message, 'error');
    }
}

async function deleteVideo(videoHash) {
    if (!confirm('确定要删除这个视频吗？')) {
        return;
    }

    const result = await apiCall(`/api/video/${videoHash}`, 'DELETE');

    if (result.success) {
        showVideoAlert(result.message, 'success');
        loadVideos();
    } else {
        showVideoAlert(result.message, 'error');
    }
}

async function clearAllVideos() {
    if (!confirm('警告: 此操作将清空所有视频数据！确定要继续吗？')) {
        return;
    }

    const result = await apiCall('/api/videos/clear', 'POST');

    if (result.success) {
        showVideoAlert(result.message, 'success');
        loadVideos();
    } else {
        showVideoAlert(result.message, 'error');
    }
}

// ========== 标签管理 ==========

async function loadTags() {
    const tableBody = document.querySelector('#tagsTable tbody');
    tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center;">加载中...</td></tr>';

    const result = await apiCall('/api/tags');

    if (result.success) {
        const tags = result.tags;

        tableBody.innerHTML = tags.map(tag => `
            <tr>
                <td>${tag.id}</td>
                <td>${tag.name}</td>
                <td>${tag.category || '--'}</td>
                <td>${tag.video_count}</td>
                <td>
                    <button class="btn btn-danger" style="padding: 5px 10px; font-size: 0.8em;" onclick="deleteTag(${tag.id})">删除</button>
                </td>
            </tr>
        `).join('');

        showTagAlert(`加载了 ${tags.length} 个标签`, 'success');
    } else {
        tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center;">加载失败: ' + result.message + '</td></tr>';
        showTagAlert('加载失败: ' + result.message, 'error');
    }
}

function showAddTagModal() {
    document.getElementById('addTagModal').classList.add('show');
}

async function addTag(event) {
    event.preventDefault();

    const btn = event.target.querySelector('button[type="submit"]');
    setButtonLoading(btn, true);

    const data = {
        name: document.getElementById('tagName').value,
        category: document.getElementById('tagCategory').value
    };

    const result = await apiCall('/api/tags/add', 'POST', data);

    setButtonLoading(btn, false);

    if (result.success) {
        showTagAlert(result.message, 'success');
        closeModal('addTagModal');
        document.getElementById('addTagForm').reset();
        loadTags();
    } else {
        showTagAlert(result.message, 'error');
    }
}

async function deleteTag(tagId) {
    if (!confirm('确定要删除这个标签吗？')) {
        return;
    }

    const result = await apiCall(`/api/tags/${tagId}`, 'DELETE');

    if (result.success) {
        showTagAlert(result.message, 'success');
        loadTags();
    } else {
        showTagAlert(result.message, 'error');
    }
}

async function clearAllTags() {
    if (!confirm('警告: 此操作将清空所有标签！确定要继续吗？')) {
        return;
    }

    // 需要添加清空标签的API
    showTagAlert('此功能暂未实现', 'warning');
}

// ========== 数据库管理 ==========

async function refreshDbStats() {
    const result = await apiCall('/api/db/stats');

    if (result.success) {
        const stats = result.stats;

        document.getElementById('videoCount').textContent = stats.video_count;
        document.getElementById('tagCount').textContent = stats.tag_count;
        document.getElementById('favoriteCount').textContent = stats.favorite_count;
        document.getElementById('viewCount').textContent = stats.view_count;
        document.getElementById('dbSize').textContent = stats.db_size_mb + ' MB';

        showDbAlert('数据已刷新', 'success');
    } else {
        showDbAlert('获取统计失败: ' + result.message, 'error');
    }
}

function confirmClear() {
    const dataTypes = ['interactions', 'favorites', 'views', 'tags', 'thumbnails', 'all'];
    const selectedTypes = [];

    let message = '请选择要清理的数据类型:\n\n';
    dataTypes.forEach((type, index) => {
        message += `${index + 1}. ${type}\n`;
    });

    const choice = prompt(message + '\n输入数字选择（多个用逗号分隔）:');

    if (choice) {
        const indices = choice.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n) && n >= 1 && n <= dataTypes.length);
        selectedTypes.push(...indices.map(i => dataTypes[i - 1]));

        if (selectedTypes.length > 0 && confirm(`确定要清理: ${selectedTypes.join(', ')} 吗？`)) {
            clearData(selectedTypes);
        }
    }
}

async function clearData(types) {
    let successCount = 0;
    let failCount = 0;

    for (const type of types) {
        const result = await apiCall('/api/db/clear', 'POST', {
            type: type,
            dry_run: false
        });

        if (result.success) {
            successCount++;
        } else {
            failCount++;
        }
    }

    if (failCount === 0) {
        showDbAlert(`成功清理 ${successCount} 项数据`, 'success');
        setTimeout(refreshDbStats, 1000);
    } else {
        showDbAlert(`清理完成: 成功 ${successCount} 项, 失败 ${failCount} 项`, 'warning');
        setTimeout(refreshDbStats, 1000);
    }
}

// ========== 日志查看 ==========

async function loadLogs(type, lines) {
    const container = document.getElementById('logsContainer');
    container.innerHTML = '<div class="log-line">加载中...</div>';

    const result = await apiCall(`/api/logs?type=${type}&lines=${lines}`);

    if (result.success) {
        container.innerHTML = result.logs.map(line => {
            let className = 'log-line';

            if (line.includes('[ERROR]') || line.includes('[CRITICAL]')) {
                className += ' error';
            } else if (line.includes('[WARNING]')) {
                className += ' warning';
            } else if (line.includes('[INFO]')) {
                className += ' info';
            }

            return `<div class="${className}">${line.trim()}</div>`;
        }).join('');

        container.scrollTop = container.scrollHeight;
    } else {
        container.innerHTML = `<div class="log-line error">加载日志失败: ${result.message}</div>`;
    }
}

async function clearLogs() {
    if (!confirm('确定要清空所有日志吗？')) {
        return;
    }

    // 需要添加清空日志的API
    alert('此功能暂未实现');
}

// ========== 初始化 ==========

document.addEventListener('DOMContentLoaded', function() {
    refreshStatus();
    refreshDbStats();

    // 每分钟自动刷新状态
    setInterval(refreshStatus, 60000);
});
