-- schema.sql
USE genealogy_db;

-- ============================================
-- 1. 用户表
-- ============================================
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. 族谱表
-- ============================================
CREATE TABLE genealogies (
    genealogy_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    surname VARCHAR(50) NOT NULL,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users (user_id)
);

-- ============================================
-- 3. 成员表
-- ============================================
CREATE TABLE members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    genealogy_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    gender ENUM('M', 'F') NOT NULL,
    birth_year INT,
    death_year INT,
    bio TEXT,
    FOREIGN KEY (genealogy_id) REFERENCES genealogies (genealogy_id)
);

-- ============================================
-- 4. 血缘关系表（邻接表模型）
-- ============================================
CREATE TABLE family_links (
    link_id INT AUTO_INCREMENT PRIMARY KEY,
    child_id INT NOT NULL,
    parent_id INT NOT NULL,
    relation_type ENUM('father', 'mother') NOT NULL,
    FOREIGN KEY (child_id) REFERENCES members (member_id),
    FOREIGN KEY (parent_id) REFERENCES members (member_id),
    UNIQUE KEY unique_parent_child (child_id, parent_id)
);

-- ============================================
-- 5. 婚姻关系表
-- ============================================
CREATE TABLE marriages (
    marriage_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id1 INT NOT NULL,
    member_id2 INT NOT NULL,
    marriage_year INT,
    divorce_year INT,
    FOREIGN KEY (member_id1) REFERENCES members (member_id),
    FOREIGN KEY (member_id2) REFERENCES members (member_id)
);

-- ============================================
-- 6. 协作表（用户-族谱 多对多）
-- ============================================
CREATE TABLE collaborations (
    collaboration_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    genealogy_id INT NOT NULL,
    role ENUM('editor', 'viewer') DEFAULT 'editor',
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (genealogy_id) REFERENCES genealogies (genealogy_id),
    UNIQUE KEY unique_collab (user_id, genealogy_id)
);

-- ============================================
-- 7. 性能优化索引
-- ============================================
-- 成员表：按族谱查询成员（最高频查询）
CREATE INDEX idx_members_genealogy ON members (genealogy_id);

-- 血缘关系表：按子女/父母查询
CREATE INDEX idx_family_links_child ON family_links (child_id);

CREATE INDEX idx_family_links_parent ON family_links (parent_id);

-- 婚姻关系表：按成员查询配偶
CREATE INDEX idx_marriages_member1 ON marriages (member_id1);

CREATE INDEX idx_marriages_member2 ON marriages (member_id2);

-- 族谱表：按创建者查询
CREATE INDEX idx_genealogies_creator ON genealogies (created_by);

-- 协作表：按族谱查询权限列表
CREATE INDEX idx_collaborations_genealogy ON collaborations (genealogy_id);