# GeneCloud 问题报告

**报告日期**: 2026年5月12日  
**基于测试**: 68个测试用例，5个失败 + 手动测试发现  
**验证方式**: 静态代码分析 + 数据库Schema对比  
**二次验证**: 2026年5月12日，通过完整源码阅读逐一验证  
**三轮验证**: 2026年5月12日，补充成员详情页面缺失问题

---

## 🔴 严重问题 (会导致崩溃)

### 问题1: relation_type 未做应用层验证导致数据库异常

**严重程度**: 🔴 严重  
**验证状态**: ✅ 已确认存在  
**位置**: `services/relation_service.py` → `dao/family_link_dao.py`  
**错误信息**: `mysql.connector.errors.DatabaseError: 1265 (01000): Data truncated for column 'relation_type' at row 1`

**问题描述**:  
当传入无效的 `relation_type` 值（如 `'biological'`）时，应用层没有进行验证就直接插入数据库。数据库中 `relation_type` 字段定义为 `ENUM('father', 'mother')`，无效值导致数据库抛出异常，且异常未被上层捕获，导致 500 错误或崩溃。

**根因分析**:

| 层级 | 文件 | 行号 | 问题 |
|------|------|------|------|
| Service层 | `services/relation_service.py` | 57 | `insert_family_link(conn, child_id, parent_id, relation_type)` 直接传递参数，无验证 |
| DAO层 | `dao/family_link_dao.py` | 32-40 | `insert_family_link` 函数没有 try-except 处理数据库异常 |
| 数据库层 | `schema.sql` | 48 | `relation_type ENUM('father', 'mother') NOT NULL` |

**复现方式**:  
⚠️ **此问题只能通过 API 接口复现，前端页面无法复现**  
原因：前端页面（`templates/genealogy_detail.html` 第74-77行）只提供"父亲"和"母亲"两个选项，无法输入其他值。但 API 接口没有对 `relation_type` 进行验证，攻击者可以通过直接调用 API 传入无效值。

```json
POST /api/relations/link
{
    "child_id": 1,
    "parent_id": 2,
    "relation_type": "biological"  // 无效值
}
```

**风险评估**:  
1. 直接调用 API 可以触发崩溃
2. 如果未来有其他客户端（移动端、第三方集成），可能触发
3. 未捕获的数据库异常会导致 500 错误，暴露内部错误信息

**建议修复**:
1. 在 `services/relation_service.py` 的 `add_parent_link` 函数中添加 `relation_type` 验证：
   ```python
   valid_types = ('father', 'mother')
   if relation_type not in valid_types:
       return None, f'relation_type 必须是 {valid_types} 之一'
   ```
2. 在 `dao/family_link_dao.py` 中添加 try-except 捕获数据库异常

---

## 🟠 高优先级问题

### 问题2: 管理员无法访问非创建的族谱统计功能

**严重程度**: 🟠 高  
**验证状态**: ✅ 已确认存在  
**位置**: `services/stats_service.py` → `get_dashboard_stats`  
**表现**: 管理员账户点击任意族谱的"统计"按钮时，弹出"无权访问"错误

**根因分析**:

| 层级 | 文件 | 行号 | 问题 |
|------|------|------|------|
| Service层 | `services/stats_service.py` | 14 | `if genealogy['created_by'] != user_id: return None, "无权访问"` |

**问题描述**:  
`get_dashboard_stats` 函数只检查了 `created_by` 字段，没有使用统一的 `check_access` 权限检查函数，完全忽略了管理员权限。

**与其他模块的对比**:
- `services/genealogy_service.py` 第38行使用 `check_access(conn, user_id, genealogy_id, 3)` ✅
- `services/member_service.py` 第15行使用 `check_access(conn, user_id, genealogy_id, 3)` ✅
- `services/stats_service.py` 第14行直接比较 `created_by != user_id` ❌

**复现步骤**:
1. 使用管理员账户登录
2. 访问一个不是自己创建的族谱
3. 点击"统计"按钮
4. 弹出"无权访问"错误

**建议修复**:
```python
def get_dashboard_stats(conn, genealogy_id, user_id):
    genealogy = find_genealogy_by_id(conn, genealogy_id)
    if not genealogy:
        return None, "族谱不存在"
    
    # 检查权限：使用统一的权限检查函数
    from services.permission_service import check_access
    ok, err = check_access(conn, user_id, genealogy_id, 3)  # level 3 = viewer
    if not ok:
        return None, "无权访问"
    
    # ... 统计逻辑
```

---

### 问题3: 成员详情页面缺失，点击"详情"按钮报 500 错误

**严重程度**: 🟠 高  
**验证状态**: ✅ 已确认存在  
**位置**: `app.py` 第46-49行 + `templates/` 目录  
**表现**: 在族谱成员列表中点击"详情"按钮后，页面跳转到 500 错误页面

**根因分析**:

| 层级 | 文件 | 行号 | 问题 |
|------|------|------|------|
| 模板链接 | `templates/genealogy_detail.html` | 181 | `<a href="/members/${m.member_id}"` 触发整页跳转 |
| 路由定义 | `app.py` | 46-49 | `member_detail_page()` 渲染 `member_detail.html` |
| **模板缺失** | `templates/member_detail.html` | — | **文件不存在** |

**问题描述**:  
前端成员列表中的"详情"按钮是一个 `<a href="/members/${m.member_id}">` 链接，会触发浏览器整页跳转。Flask 路由 `member_detail_page` 尝试渲染 `member_detail.html` 模板，但 `templates/` 目录下根本不存在该文件，Flask 抛出 `jinja2.exceptions.TemplateNotFound` 异常，最终返回 500 错误页面。

**涉及代码**:

前端按钮（`templates/genealogy_detail.html` 第181-182行）:
```javascript
<a href="/members/${m.member_id}"
   class="btn btn-sm btn-outline-primary">详情</a>
```

后端路由（`app.py` 第46-49行）:
```python
@app.route('/members/<int:member_id>')
def member_detail_page(member_id):
    """成员详情页"""
    return render_template('member_detail.html', member_id=member_id)
```

API接口（`routes/member_routes.py` 第36-50行）:
```python
@member_bp.route('/api/members/<int:member_id>')
def api_get_member(member_id):
    """获取成员详情"""
    # ✅ 此 API 接口正常工作，返回 JSON 数据
```

**问题闭环**:
1. 用户在族谱详情页点击"详情"按钮
2. 浏览器跳转到 `/members/<member_id>`（注意：不是 API 路由）
3. Flask 执行 `member_detail_page()` 并调用 `render_template('member_detail.html')`
4. **`templates/member_detail.html` 不存在** → Flask 抛出 `TemplateNotFound` → 500 错误

**与其他已存在模板的对比**:
- `templates/genealogy_detail.html` ✅ 存在
- `templates/genealogy_list.html` ✅ 存在
- `templates/login.html` ✅ 存在
- `templates/dashboard.html` ✅ 存在
- `templates/member_detail.html` ❌ **缺失**

**建议修复**:

方案一（推荐）：创建 `templates/member_detail.html` 模板，实现完整的成员详情展示页面，页面内通过 JavaScript 调用 `/api/members/<member_id>` API 获取数据并渲染。

方案二（快速修复）：将"详情"按钮改为 JavaScript 弹窗，在当前页面内通过 `fetch('/api/members/${m.member_id}')` 获取并展示成员详情，无需页面跳转。

---

### 问题4: 前端缺少删除族谱成员的功能

**严重程度**: 🟠 高  
**验证状态**: ✅ 已确认存在  
**位置**: `templates/genealogy_detail.html` 第165-186行  
**表现**: 族谱成员列表中没有删除按钮，无法通过前端界面删除成员

**根因分析**:

| 文件 | 行号 | 问题 |
|------|------|------|
| `templates/genealogy_detail.html` | 180-183 | 操作列只有"详情"按钮，没有"删除"按钮 |
| `routes/member_routes.py` | 123-136 | 后端 `DELETE /api/members/<member_id>` 已实现 ✅ |
| `services/member_service.py` | 82-93 | `remove_member` 函数已实现 ✅ |

**现有前端代码** (`templates/genealogy_detail.html` 第171-186行):
```javascript
container.innerHTML = '<table class="table table-striped"><thead><tr>'
    + '<th>ID</th><th>姓名</th><th>性别</th><th>出生年</th><th>死亡年</th><th>操作</th>'
    + '</tr></thead><tbody>' + members.map(m => `
    <tr>
        <td>${m.member_id}</td>
        <td>${m.name}</td>
        <td>${m.gender === 'M' ? '男' : '女'}</td>
        <td>${m.birth_year || '-'}</td>
        <td>${m.death_year || '在世'}</td>
        <td>
            <a href="/members/${m.member_id}"
               class="btn btn-sm btn-outline-primary">详情</a>  <!-- 只有详情按钮 -->
        </td>
    </tr>
`).join('') + '</tbody></table>';
```

**影响**:
1. 用户无法删除错误录入的成员
2. 数据库中的成员只能通过直接操作数据库或 API 来删除
3. 用户体验差，无法管理成员数据

**建议修复**:
在成员列表的操作列中添加删除按钮，并添加删除函数：

```javascript
container.innerHTML = '<table class="table table-striped"><thead><tr>'
    + '<th>ID</th><th>姓名</th><th>性别</th><th>出生年</th><th>死亡年</th><th>操作</th>'
    + '</tr></thead><tbody>' + members.map(m => `
    <tr>
        <td>${m.member_id}</td>
        <td>${m.name}</td>
        <td>${m.gender === 'M' ? '男' : '女'}</td>
        <td>${m.birth_year || '-'}</td>
        <td>${m.death_year || '在世'}</td>
        <td>
            <a href="/members/${m.member_id}"
               class="btn btn-sm btn-outline-primary">详情</a>
            <button class="btn btn-sm btn-outline-danger" 
                    onclick="deleteMember(${m.member_id})">删除</button>
        </td>
    </tr>
`).join('') + '</tbody></table>';

async function deleteMember(memberId) {
    if (!confirm('确定要删除该成员吗？此操作不可恢复。')) return;
    const result = await api(`/api/members/${memberId}`, 'DELETE');
    if (result.error) { alert(result.error); return; }
    loadMembers();  // 刷新成员列表
}
```

---

### 问题5: 前端缺少编辑族谱成员的功能

**严重程度**: 🟠 高  
**验证状态**: ✅ 已确认存在  
**位置**: `templates/genealogy_detail.html` 第165-186行  
**表现**: 族谱成员列表中没有编辑按钮，无法通过前端界面修改成员信息

**根因分析**:

| 文件 | 行号 | 问题 |
|------|------|------|
| `templates/genealogy_detail.html` | 180-183 | 操作列只有"详情"按钮，没有"编辑"按钮 |
| `routes/member_routes.py` | 97-120 | 后端 `PUT /api/members/<member_id>` 已实现 ✅ |
| `services/member_service.py` | 67-79 | `modify_member` 函数已实现 ✅ |

**影响**:
1. 用户无法修改错误录入的成员信息
2. 成员信息一旦添加就无法通过界面修改
3. 用户体验差

**建议修复**:
在成员列表的操作列中添加编辑按钮：
```javascript
<td>
    <a href="/members/${m.member_id}"
       class="btn btn-sm btn-outline-primary">详情</a>
    <button class="btn btn-sm btn-outline-warning" 
            onclick="editMember(${m.member_id})">编辑</button>
    <button class="btn btn-sm btn-outline-danger" 
            onclick="deleteMember(${m.member_id})">删除</button>
</td>
```

---

### 问题6: 权限赋予功能失败

**严重程度**: 🟠 高  
**验证状态**: ✅ 已确认存在  
**位置**: `services/permission_service.py` + `schema.sql`  
**表现**: 以 owner 身份向其他用户赋予 editor 权限时返回 400 错误

**根因分析**:

| 层级 | 文件 | 行号 | 问题 |
|------|------|------|------|
| 数据库层 | `schema.sql` | 74 | `role ENUM('editor', 'viewer') DEFAULT 'editor'` 缺少 `admin` 和 `owner` |
| 迁移脚本 | `db_migrate.py` | 19 | `ALTER TABLE collaborations MODIFY COLUMN role ENUM('admin','owner','editor')` 修复此问题 |
| DAO层 | `dao/permission_dao.py` | 40-45 | `grant_permission` 使用 `ON DUPLICATE KEY UPDATE` 插入 `owner` 会失败 |

**问题描述**:  
1. `schema.sql` 中 `collaborations.role` 定义为 `ENUM('editor', 'viewer')`，不包含 `admin` 和 `owner`
2. 当调用 `grant_permission(conn, user_id, genealogy_id, 'owner')` 时，MySQL 会拒绝插入无效的 ENUM 值
3. `db_migrate.py` 才能修复此问题，需要先执行迁移脚本

**复现步骤**:
1. 确保未执行 `db_migrate.py`
2. 创建新族谱
3. 尝试为其他用户赋予 `editor` 或 `owner` 权限
4. 返回 400 错误

**建议修复**:
1. 更新 `schema.sql` 中的 `collaborations` 表定义
2. 确保所有环境都执行了 `db_migrate.py` 迁移脚本

---

### 问题7: 自引用关系未被阻止

**严重程度**: 🟠 高  
**验证状态**: ✅ 已确认存在  
**位置**: `services/relation_service.py` → `add_parent_link`  
**表现**: 用户可以将自己设为自己的父/母亲，返回 201 成功

**根因分析**:

| 层级 | 文件 | 行号 | 问题 |
|------|------|------|------|
| Service层 | `services/relation_service.py` | 41-58 | `add_parent_link` 函数没有检查 `child_id == parent_id` |

**问题代码** (`services/relation_service.py` 第41-58行):
```python
def add_parent_link(conn, child_id, parent_id, relation_type, user_id):
    """建立亲子关系"""
    child = find_member_by_id(conn, child_id)
    parent = find_member_by_id(conn, parent_id)

    if not child or not parent:
        return None, "成员不存在"

    # 两人必须在同一个族谱
    if child['genealogy_id'] != parent['genealogy_id']:
        return None, "父母和子女必须在同一个族谱"

    ok, err = check_access(conn, user_id, child['genealogy_id'], 3)
    if not ok:
        return None, err

    # ❌ 缺少: if child_id == parent_id 的检查
    insert_family_link(conn, child_id, parent_id, relation_type)
    return {'message': '关系建立成功'}, None
```

**测试验证**: `tests/test_relation.py` 第107-117行 `test_add_link_self_parent` 测试期望返回 400/409，但当前代码会返回 201。

**建议修复**:
在函数开头添加检查：
```python
def add_parent_link(conn, child_id, parent_id, relation_type, user_id):
    # ... 前面的代码 ...
    
    if child_id == parent_id:
        return None, '不能将自己设为自己的父母'
    
    # ... 后面的代码 ...
```

---

## 🟡 中优先级问题

### 问题8: 出生年份未验证未来日期

**严重程度**: 🟡 中  
**验证状态**: ✅ 已确认存在  
**位置**: `services/member_service.py` → `create_member`  
**表现**: 可以创建出生年份为 2030 年的成员

**根因分析**:

| 层级 | 文件 | 行号 | 问题 |
|------|------|------|------|
| Service层 | `services/member_service.py` | 57 | `if birth_year and (birth_year < 1 or birth_year > 2100):` |

**问题代码** (`services/member_service.py` 第57行):
```python
if birth_year and (birth_year < 1 or birth_year > 2100):
    return None, "出生年份不合理"
```

**问题**:  
验证条件 `birth_year > 2100` 过于宽松，允许创建出生年份为 2030 年的成员。

**建议修复**:
```python
import datetime

def create_member(conn, genealogy_id, name, gender, birth_year,
                  death_year, bio, user_id):
    # ... 前面的代码 ...
    
    current_year = datetime.datetime.now().year
    if birth_year and birth_year > current_year:
        return None, '出生年份不能在未来'
    
    # ... 后面的代码 ...
```

---

### 问题9: 亲缘查询功能异常（测试代码缺陷）

**严重程度**: 🟡 中  
**验证状态**: ✅ 已确认存在  
**位置**: `tests/test_relation.py` → `TestQueryKinship.test_query_kinship_success`  
**表现**: 查询两个有亲缘关系的成员时返回 400 错误

**根因分析**:

| 层级 | 文件 | 行号 | 问题 |
|------|------|------|------|
| Test层 | `tests/test_relation.py` | 181-188 | 测试用例逻辑缺陷：未建立关系就查询亲缘 |

**问题代码** (`tests/test_relation.py` 第181-188行):
```python
def test_query_kinship_success(self, logged_in_client):
    """Test querying kinship path."""
    gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
    if pid and cid:
        # ❌ 缺少: 调用 POST /api/relations/link 建立亲子关系
        resp = logged_in_client.get(
            f'/api/relations/kinship?member_a={pid}&member_b={cid}'
        )
        assert resp.status_code == 200
```

**实际根因**:  
测试用例 `test_query_kinship_success` 在调用 `create_test_genealogy_and_members` 创建两个独立成员后，**没有先调用 POST `/api/relations/link` 建立亲子关系**就直接查询亲缘。

- `query_kinship` → `find_kinship_path` 在数据库中找不到两人之间的路径
- `find_kinship_path` 返回 `None`（第148行：`return None  # 没有亲缘关系`）
- `query_kinship` 返回 `None, "两人之间没有亲缘关系"` + 400 状态码
- 测试期望 200 但实际得到 400，测试失败

**与其他测试的对比**:  
同文件中 `test_query_ancestors_success`（第141-150行）和 `test_query_descendants_success`（第161-170行）都**正确地**在查询前建立了关系：
```python
# 正确示例 - test_query_ancestors_success
if pid and cid:
    # 先建立关系 ✅
    logged_in_client.post('/api/relations/link', json={
        'child_id': cid, 'parent_id': pid, 'relation_type': 'father'
    })
    # 再查询
    resp = logged_in_client.get(f'/api/members/{cid}/ancestors')
    assert resp.status_code == 200
```

**建议修复**:
在 `test_query_kinship_success` 中添加建立关系的代码：
```python
def test_query_kinship_success(self, logged_in_client):
    """Test querying kinship path."""
    gid, pid, cid = create_test_genealogy_and_members(logged_in_client)
    if pid and cid:
        # ✅ 先建立亲子关系
        logged_in_client.post('/api/relations/link', json={
            'child_id': cid, 'parent_id': pid, 'relation_type': 'father'
        })
        # 再查询亲缘
        resp = logged_in_client.get(
            f'/api/relations/kinship?member_a={pid}&member_b={cid}'
        )
        assert resp.status_code == 200
```

**结论**: 这是一个**测试代码的 bug**，而非服务端功能的 bug。服务端的亲缘查询逻辑本身是正确的。

---

## 🟢 低优先级 / 建议改进

### 问题10: 密码使用简单 SHA256 哈希

**严重程度**: 🟢 低（实验项目可接受）  
**验证状态**: ✅ 已确认存在  
**位置**: `services/auth_service.py` 第9-11行

**验证代码**:
```python
def _hash_password(password):
    """简单哈希密码（实验用，生产环境请用 bcrypt）"""
    return hashlib.sha256(password.encode()).hexdigest()
```

**建议**: 生产环境应使用 bcrypt 或 argon2 等慢哈希算法

---

### 问题11: 登出接口在未登录时仍返回 200

**严重程度**: 🟢 低  
**验证状态**: ✅ 已确认存在  
**位置**: `routes/auth_routes.py` 第59-63行

**验证代码**:
```python
@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    """登出接口"""
    session.clear()
    return jsonify({'message': '已登出'}), 200  # 未检查 session 是否存在
```

**建议**: 可以考虑检查 session 是否是否存在，不存在时返回 401 或直接返回成功

---

### 问题12: SECRET_KEY 硬编码在代码中

**严重程度**: 🟢 低（实验项目可接受）  
**验证状态**: ✅ 已确认存在  
**位置**: `config.py` 第17行

**验证代码**:
```python
SECRET_KEY = 'your-secret-key-change-in-production'
```

**建议**: 生产环境应从环境变量读取

---

### 问题13: 数据库密码硬编码

**严重程度**: 🟢 低（实验项目可接受）  
**验证状态**: ✅ 已确认存在  
**位置**: `config.py` 第7-14行

**验证代码**:
```python
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',       # 硬编码密码
    'database': 'genealogy_db',
    'charset': 'utf8mb4',
}
```

**建议**: 生产环境应从环境变量读取

---

## 📋 问题汇总

| 优先级 | 数量 | 问题编号 |
|--------|------|----------|
| 🔴 严重 | 1 | #1 |
| 🟠 高 | 6 | #2, #3, #4, #5, #6, #7 |
| 🟡 中 | 2 | #8, #9 |
| 🟢 低 | 4 | #10, #11, #12, #13 |

---

## 🎯 推荐修复顺序

1. **问题 #1** (relation_type 验证) - 防止数据库崩溃，严重程度最高
2. **问题 #3** (成员详情页面缺失) - 点击详情按钮必报错，核心功能不可用
3. **问题 #2** (管理员统计权限) - 核心功能阻塞，用户体验严重受损
4. **问题 #6** (权限赋予) - 核心功能不可用，需先执行迁移脚本
5. **问题 #4** (删除成员功能缺失) - 基本 CRUD 功能不完整
6. **问题 #5** (编辑成员功能缺失) - 基本 CRUD 功能不完整
7. **问题 #7** (自引用检测) - 数据完整性
8. **问题 #8** (出生年份验证) - 数据合理性
9. **问题 #9** (测试代码修复) - 测试正确性
10. **问题 #10-13** - 安全性改进（实验项目可后续处理）

---

## 🔍 根本原因分析

### 问题类型分布

| 根因类型 | 涉及问题 | 占比 |
|---------|---------|------|
| 输入验证缺失 | #1, #7, #8 | 23.1% |
| 权限逻辑不完整 | #2 | 7.7% |
| 数据库Schema与代码不一致 | #6 | 7.7% |
| 前端功能缺失/模板文件缺失 | #3, #4, #5 | 23.1% |
| 测试代码缺陷 | #9 | 7.7% |
| 安全性配置 | #10, #11, #12, #13 | 30.8% |

### 代码层面根因

1. **Service层验证不足**: 多个业务函数缺少必要的输入验证（#1, #7, #8）
2. **权限检查不一致**: 统计功能未使用统一的 `check_access` 函数（#2）
3. **数据库迁移缺失**: `schema.sql` 与实际需要的 ENUM 不一致（#6）
4. **前端功能不完整**: 只实现了部分 CRUD 操作，且缺少成员详情页面（#3, #4, #5）
5. **测试代码缺陷**: 测试用例缺少前置条件（建立关系）导致断言失败（#9）
6. **安全配置**: 实验性质项目，硬编码密钥和简单哈希（#10-13）

---

## 📝 验证说明

本报告在 2026年5月12日 进行了三轮验证，通过完整阅读源代码确认所有13个问题均真实存在。

| 问题 | 验证结果 | 验证方式 |
|------|---------|---------|
| #1 | ✅ 确认存在 | 阅读 `relation_service.py:57`, `family_link_dao.py:32-40`, `schema.sql:48` |
| #2 | ✅ 确认存在 | 阅读 `stats_service.py:14`，对比其他模块的 `check_access` 调用 |
| #3 | ✅ 确认存在 | 阅读 `app.py:46-49`，检查 `templates/` 目录确认 `member_detail.html` 不存在 |
| #4 | ✅ 确认存在 | 阅读 `genealogy_detail.html`，确认操作列只有"详情"按钮 |
| #5 | ✅ 确认存在 | 同上 |
| #6 | ✅ 确认存在 | 阅读 `schema.sql:74`，确认 ENUM 不包含 'admin' 和 'owner' |
| #7 | ✅ 确认存在 | 阅读 `relation_service.py:41-58`，确认缺少自引用检查 |
| #8 | ✅ 确认存在 | 阅读 `member_service.py:57`，确认上界为 2100 |
| #9 | ✅ 确认存在 | 阅读 `test_relation.py:181-188`，确认测试缺少建立关系步骤 |
| #10 | ✅ 确认存在 | 阅读 `auth_service.py:9-11`，确认使用 `hashlib.sha256` |
| #11 | ✅ 确认存在 | 阅读 `auth_routes.py:59-63`，确认未检查 session |
| #12 | ✅ 确认存在 | 阅读 `config.py:17`，确认硬编码 |
| #13 | ✅ 确认存在 | 阅读 `config.py:11`，确认硬编码 |

**关于问题3的特别说明**:  
前端成员列表的"详情"按钮使用 `<a href="/members/${m.member_id}">` 进行整页跳转，Flask 路由已定义（`app.py` 第46-49行），但对应的模板文件 `templates/member_detail.html` 不存在，导致每次点击"详情"都会触发 500 错误。API 接口 `/api/members/<member_id>` 本身工作正常（返回 JSON），但没有对应的前端页面来消费这些数据。

**关于问题9的特别说明**:  
原报告推测根因是"session/cookie 未正确传递导致权限检查失败"，经源码验证后确认实际根因是**测试用例缺少前置条件**。`test_query_kinship_success` 在查询亲缘前未建立亲子关系，导致服务端返回"两人之间没有亲缘关系"错误（400）。这是一个**测试代码的 bug**，服务端的亲缘查询逻辑本身是正确的。