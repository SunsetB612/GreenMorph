# GreenMorph 数据库设计

## 数据库表结构

### 1. 用户表 (users)
```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_filename VARCHAR(255),
    bio TEXT,
    skill_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'beginner',
    points INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);
```

**字段说明**:
- `id` - 用户唯一标识符
- `username` - 用户名（用于登录和显示）
- `email` - 邮箱地址（用于登录）
- `password_hash` - 加密后的密码
- `avatar_filename` - 头像文件名（存储在 input/avatars/ 目录）
- `bio` - 个人简介
- `skill_level` - 技能等级（新手/中级/高级）
- `points` - 用户积分
- `is_active` - 账户是否激活

### 2. 改造项目表 (redesign_projects)
```sql
CREATE TABLE redesign_projects (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    original_image_filename VARCHAR(255),
    final_image_filename VARCHAR(255),
    target_style VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**字段说明**:
- `id` - 项目唯一标识符
- `user_id` - 项目创建者ID
- `title` - 项目标题
- `original_image_filename` - 改造前图片文件名（存储在 input/redesign_projects/ 目录）
- `final_image_filename` - 改造后效果图文件名（存储在 output/redesign_projects/ 目录）
- `target_style` - 目标风格

### 3. 社区帖子表 (posts)
```sql
CREATE TABLE posts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    images JSON,
    likes_count INT DEFAULT 0,
    comments_count INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**字段说明**:
- `id` - 帖子唯一标识符
- `user_id` - 发帖用户ID
- `title` - 帖子标题
- `content` - 帖子正文内容
- `images` - 帖子中的图片文件名列表（JSON格式，存储在 input/posts/ 目录）
- `likes_count` - 获得的点赞数
- `comments_count` - 评论数量

### 4. 评论表 (comments)
```sql
CREATE TABLE comments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    post_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**字段说明**:
- `id` - 评论唯一标识符
- `post_id` - 被评论的帖子ID
- `user_id` - 评论者ID
- `content` - 评论内容

### 5. 点赞表 (likes)
```sql
CREATE TABLE likes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    target_type ENUM('post', 'comment') NOT NULL,
    target_id BIGINT NOT NULL,
    UNIQUE KEY unique_like (user_id, target_type, target_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**字段说明**:
- `id` - 点赞记录唯一标识符
- `user_id` - 点赞用户ID
- `target_type` - 点赞目标类型（post/comment）
- `target_id` - 被点赞内容的ID

### 6. 成就表 (achievements)
```sql
CREATE TABLE achievements (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_filename VARCHAR(255),
    condition_type ENUM('project_count', 'post_count', 'likes_received') NOT NULL,
    condition_value INT NOT NULL,
    points INT DEFAULT 10
);
```

**字段说明**:
- `id` - 成就唯一标识符
- `name` - 成就名称
- `description` - 成就描述
- `icon_filename` - 成就图标文件名
- `condition_type` - 获得条件类型（项目数量/发帖数量/获得点赞数）
- `condition_value` - 获得条件数值
- `points` - 奖励积分

### 7. 用户成就表 (user_achievements)
```sql
CREATE TABLE user_achievements (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    achievement_id BIGINT NOT NULL,
    UNIQUE KEY unique_user_achievement (user_id, achievement_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
);
```

**字段说明**:
- `id` - 记录唯一标识符
- `user_id` - 用户ID
- `achievement_id` - 成就ID

## 索引设计

```sql
-- 用户表索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- 项目表索引
CREATE INDEX idx_redesign_projects_user_id ON redesign_projects(user_id);

-- 帖子表索引
CREATE INDEX idx_posts_user_id ON posts(user_id);

-- 评论表索引
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);

-- 点赞表索引
CREATE INDEX idx_likes_user_id ON likes(user_id);
CREATE INDEX idx_likes_target ON likes(target_type, target_id);
```

## 表关系

```
users (1) ──→ (N) redesign_projects     # 一个用户可以有多个改造项目
users (1) ──→ (N) posts                # 一个用户可以发多个帖子
users (1) ──→ (N) comments             # 一个用户可以发多个评论
users (1) ──→ (N) likes                # 一个用户可以点多个赞
users (1) ──→ (N) user_achievements    # 一个用户可以有多个成就

posts (1) ──→ (N) comments             # 一个帖子可以有多个评论
posts (1) ──→ (N) likes                # 一个帖子可以被多次点赞
comments (1) ──→ (N) likes             # 一个评论可以被多次点赞

achievements (1) ──→ (N) user_achievements  # 一个成就可以被多个用户获得
```

## 文件存储结构

```
input/                      # 用户上传的原始文件
├── avatars/               # 用户头像
├── redesign_projects/     # 改造项目原始图片
└── posts/                 # 帖子图片

output/                    # AI生成的图片
├── redesign_projects/     # 改造效果图
└── steps/                 # 改造步骤图
```

## 核心功能模块

- **用户系统** - 注册、登录、个人资料管理
- **改造项目** - 旧物改造项目创建和管理
- **社区功能** - 发帖、评论、点赞互动
- **激励系统** - 积分、成就、徽章系统
- **文件管理** - 图片上传和存储管理