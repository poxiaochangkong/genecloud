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