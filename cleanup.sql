-- 清理无效的视频标签关联（video_id 指向不存在的视频）
DELETE FROM video_tags
WHERE video_id NOT IN (SELECT id FROM videos);

-- 清理无效的用户交互记录（video_id 指向不存在的视频）
DELETE FROM user_interactions
WHERE video_id NOT IN (SELECT id FROM videos);

-- 清理无效的用户偏好（tag_id 指向不存在的标签）
DELETE FROM user_preferences
WHERE tag_id NOT IN (SELECT id FROM tags);
