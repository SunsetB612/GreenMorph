# GreenMorph 数据库设计 v3.0 - 完整版

## 优化后的数据库表结构

### 1. 用户表 (users) - 保持不变
```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    bio TEXT,
    skill_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'beginner',
    points INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 2. 用户输入图片表 (input_images)
```sql
CREATE TABLE input_images (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    original_filename VARCHAR(255),
    input_image_path VARCHAR(500) NOT NULL,
    input_image_size INT,
    mime_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 3. 用户输入需求表 (input_demand)
```sql
CREATE TABLE input_demand (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    demand TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 4. 改造项目表 (redesign_projects)
```sql
CREATE TABLE redesign_projects (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    project_name VARCHAR(200) NOT NULL,
    input_image_id BIGINT,
    input_demand_id BIGINT,
    
    -- 生成的文件
    output_image_path VARCHAR(500),
    output_pdf_path VARCHAR(500),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (input_image_id) REFERENCES input_images(id) ON DELETE SET NULL,
    FOREIGN KEY (input_demand_id) REFERENCES input_demand(id) ON DELETE SET NULL
);
```

### 5. 改造步骤表 (redesign_steps)
```sql
CREATE TABLE redesign_steps (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL,
    step_number INT NOT NULL,
    description TEXT NOT NULL,
    step_image_path VARCHAR(500),
    
    FOREIGN KEY (project_id) REFERENCES redesign_projects(id) ON DELETE CASCADE,
    INDEX idx_project_step (project_id, step_number)
);
```

### 6. 项目详情表 (project_details)
```sql
CREATE TABLE project_details (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL,
    total_cost_estimate TEXT,
    total_time_estimate TEXT,
    difficulty_level VARCHAR(20),
    materials_and_tools TEXT,
    safety_notes TEXT,
    tips TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES redesign_projects(id) ON DELETE CASCADE
);
```

### 7. 社区帖子表 (posts) - 优化版
```sql
CREATE TABLE posts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    likes_count INT DEFAULT 0,
    comments_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 8. 评论表 (comments) - 优化版
```sql
CREATE TABLE comments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    post_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 9. 社区图片表 (community_images) - 新增
```sql
CREATE TABLE community_images (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    uploader_id BIGINT NOT NULL,
    original_filename VARCHAR(255),
    file_path VARCHAR(500) NOT NULL,
    file_size INT,
    mime_type VARCHAR(100),
    image_type ENUM('post', 'comment') NOT NULL,
    target_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_target (image_type, target_id),
    INDEX idx_uploader (uploader_id)
);
```

### 10. 点赞表 (likes) - 保持不变
```sql
CREATE TABLE likes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    target_type ENUM('post', 'comment') NOT NULL,
    target_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_like (user_id, target_type, target_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 11. 成就表 (achievements) - 保持不变
```sql
CREATE TABLE achievements (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_filename VARCHAR(255),
    condition_type ENUM('project_count', 'post_count', 'likes_received') NOT NULL,
    condition_value INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 12. 用户成就表 (user_achievements) - 保持不变
```sql
CREATE TABLE user_achievements (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    achievement_id BIGINT NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_achievement (user_id, achievement_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
);
```

## 主要改进点

### 1. **完整的项目管理**
- `redesign_projects` 表存储完整的改造项目信息
- 包含最终效果图和PDF说明书路径
- 支持项目状态跟踪

### 2. **详细的步骤信息**
- `redesign_steps` 表存储每个步骤的完整信息
- 包含文本说明、图片、材料、工具、成本、安全注意事项
- 支持步骤排序和编号

### 3. **文件存储策略**
- 用户改造项目图片：`static/users/{userid}/input/` 和 `static/users/{userid}/output/`
- 社区帖子图片：`static/community/posts/{post_id}/`
- 评论图片：`static/community/comments/{comment_id}/`
- 原始图片记录：`input_images` 表
- 最终效果图：`redesign_projects.output_image_path`
- 步骤图：`redesign_steps.step_image_path`
- 社区图片：`community_images` 表

### 4. **数据关联清晰**
- 通过外键关联输入和输出
- 支持一个项目对应多个步骤
- 便于数据追溯和审计

### 5. **积分系统设计**
- 用户积分存储在 `users.points` 字段
- 完成项目后，积分累加到用户账户
- 成就系统基于用户行为触发，不直接存储积分

## 工作流程

### 1. **用户输入阶段**
```
用户上传图片 → input_images 表
用户输入需求 → input_text 表
```

### 2. **AI处理阶段**
```
图片分析 → 生成改造方案 → 生成图像 → 生成PDF
```

### 3. **结果存储阶段**
```
最终效果图 → redesign_projects.output_image_path
PDF说明书 → redesign_projects.output_pdf_path
步骤信息 → redesign_steps 表
```

### 4. **用户下载阶段**
```
用户查看项目 → 下载PDF说明书 → 查看步骤详情
```

## 优势

1. **完整性**：支持完整的改造项目生命周期
2. **可追溯**：所有输入输出都有记录
3. **用户友好**：支持PDF下载和步骤查看
4. **扩展性**：易于添加新功能
5. **性能优化**：合理的索引和关联设计

这个设计更符合你的完整需求！
