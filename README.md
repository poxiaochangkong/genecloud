# 🌳 GeneCloud - 寻根溯源族谱管理系统

一个基于 Flask 和 MySQL 的族谱管理系统，帮助用户记录、管理和探索家族历史与血缘关系。

## ✨ 功能特性

- **用户认证系统** - 注册、登录、会话管理
- **族谱管理** - 创建、编辑、删除族谱
- **成员管理** - 管理家族成员信息
- **关系管理** - 记录和查询家族成员之间的关系（婚姻、亲子等）
- **权限控制** - 管理员权限转让与管理
- **数据统计** - 族谱数据统计分析
- **响应式界面** - 基于 Jinja2 模板的 Web 界面

## 🏗️ 项目结构

```
genecloud/
├── app.py                  # Flask 应用入口
├── config.py               # 配置文件（数据库、密钥等）
├── schema.sql              # 数据库初始化脚本
├── init_admin.py           # 管理员初始化脚本
├── db_migrate.py           # 数据库迁移脚本
├── requirements.txt        # Python 依赖
│
├── models/                 # 数据模型层
│   ├── user.py             # 用户模型
│   ├── genealogy.py        # 族谱模型
│   ├── member.py           # 成员模型
│   ├── family_link.py      # 家庭关系模型
│   └── marriage.py         # 婚姻关系模型
│
├── dao/                    # 数据访问层 (Data Access Object)
│   ├── db.py               # 数据库连接管理
│   ├── user_dao.py         # 用户数据操作
│   ├── genealogy_dao.py    # 族谱数据操作
│   ├── member_dao.py       # 成员数据操作
│   ├── family_link_dao.py  # 家庭关系数据操作
│   ├── marriage_dao.py     # 婚姻关系数据操作
│   └── permission_dao.py   # 权限数据操作
│
├── services/               # 业务逻辑层
│   ├── auth_service.py     # 认证服务
│   ├── genealogy_service.py# 族谱服务
│   ├── member_service.py   # 成员服务
│   ├── relation_service.py # 关系服务
│   ├── permission_service.py# 权限服务
│   └── stats_service.py    # 统计服务
│
├── routes/                 # 路由层（控制器）
│   ├── auth_routes.py      # 认证路由
│   ├── genealogy_routes.py # 族谱路由
│   ├── member_routes.py    # 成员路由
│   └── relation_routes.py  # 关系路由
│
├── templates/              # HTML 模板
│   ├── base.html           # 基础模板
│   ├── login.html          # 登录页面
│   ├── dashboard.html      # 仪表盘页面
│   ├── genealogy_list.html # 族谱列表页面
│   └── genealogy_detail.html# 族谱详情页面
│
└── static/                 # 静态资源（CSS、JS、图片等）
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+ 或 MySQL 8.0
- pip（Python 包管理器）

### 安装步骤

1. **克隆项目**

   ```bash
   git clone git@github.com:poxiaochangkong/genecloud.git
   cd genecloud
   ```

2. **创建虚拟环境并激活**

   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

4. **配置数据库**

   编辑 `config.py` 文件，修改数据库连接信息：

   ```python
   DATABASE_CONFIG = {
       'host': 'localhost',
       'port': 3306,
       'user': 'root',
       'password': 'your_password',  # 改成你的MySQL密码
       'database': 'genealogy_db',
       'charset': 'utf8mb4',
   }
   ```

5. **初始化数据库**

   ```bash
   mysql -u root -p < schema.sql
   ```

6. **初始化管理员账户**

   ```bash
   python init_admin.py
   ```

7. **启动应用**

   ```bash
   python app.py
   ```

8. **访问应用**

   打开浏览器访问 http://localhost:5000

## 📋 API 接口

### 认证相关

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/login` | 用户登录 |
| POST | `/api/logout` | 用户登出 |
| POST | `/api/register` | 用户注册 |

### 族谱管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/genealogies` | 获取族谱列表 |
| POST | `/api/genealogies` | 创建族谱 |
| GET | `/api/genealogies/<id>` | 获取族谱详情 |
| PUT | `/api/genealogies/<id>` | 更新族谱 |
| DELETE | `/api/genealogies/<id>` | 删除族谱 |

### 成员管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/genealogies/<id>/members` | 获取成员列表 |
| POST | `/api/genealogies/<id>/members` | 添加成员 |
| GET | `/api/members/<id>` | 获取成员详情 |
| PUT | `/api/members/<id>` | 更新成员信息 |
| DELETE | `/api/members/<id>` | 删除成员 |

### 关系管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/relations` | 获取关系列表 |
| POST | `/api/relations` | 创建关系 |
| DELETE | `/api/relations/<id>` | 删除关系 |

### 管理员 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/admin/current` | 获取当前管理员信息 |
| POST | `/api/admin/transfer` | 转让管理员权限 |

## 🗄️ 数据库结构

### 主要表

- **users** - 用户表
- **genealogies** - 族谱表
- **members** - 成员表
- **family_links** - 家庭关系表
- **marriages** - 婚姻关系表
- **permissions** - 权限表

详细的数据库结构请参考 `schema.sql` 文件。

## 🔧 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_CONFIG` | 数据库连接配置 | 见 config.py |
| `SECRET_KEY` | Flask 会话密钥 | 需要在生产环境中修改 |

## 🛠️ 开发指南

### 代码结构

项目采用三层架构：

1. **Routes（路由层）** - 处理 HTTP 请求和响应
2. **Services（服务层）** - 实现业务逻辑
3. **DAO（数据访问层）** - 负责数据库操作
4. **Models（模型层）** - 定义数据结构

### 添加新功能

1. 在 `models/` 目录添加数据模型
2. 在 `dao/` 目录添加数据访问方法
3. 在 `services/` 目录添加业务逻辑
4. 在 `routes/` 目录添加路由处理
5. 在 `templates/` 目录添加 HTML 模板（如需要）

## ⚠️ 注意事项

- 在生产环境中，请修改 `config.py` 中的 `SECRET_KEY`
- 请确保 MySQL 服务已启动并可访问
- 首次运行需要初始化数据库和管理员账户

## 📄 许可证

本项目仅用于学习和实验目的。

## 👥 贡献者

- poxiaochangkong

---

**注意：** 本项目是数据库应用实践课程的实验项目，用于学习 Flask Web 开发和数据库操作。