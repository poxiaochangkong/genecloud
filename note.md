# SQL语法笔记 — 寻根溯源族谱管理系统

以下是对`schema.sql`中涉及的SQL语法的详细解释。

## 1. `INT AUTO_INCREMENT PRIMARY KEY` 的作用

- **INT**: 整数数据类型，用于存储整数值。
- **AUTO_INCREMENT**: 自动递增属性。当向表中插入新行时，如果没有为该列指定值，数据库会自动生成一个唯一的递增整数（通常从1开始）。这常用于生成主键值，确保每一行都有唯一标识。
- **PRIMARY KEY**: 主键约束。主键唯一标识表中的每一行，不允许有重复值，也不允许为NULL。一个表只能有一个主键。

**示例**：在`users`表中，`user_id`列使用此组合，意味着每个新用户都会自动分配一个唯一的ID，如1, 2, 3等。

## 2. `NOT NULL UNIQUE` 的作用

- **NOT NULL**: 非空约束，确保该列不能包含NULL值。插入或更新数据时，必须为该列提供一个值。
- **UNIQUE**: 唯一约束，确保该列中的所有值都是唯一的，不能有重复。但允许有NULL值（除非同时有NOT NULL约束）。

**示例**：在`users`表的`username`列上使用`NOT NULL UNIQUE`，表示用户名必须提供，且不能重复。

## 3. `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` 的作用

- **TIMESTAMP**: 日期和时间数据类型，存储日期和时间（格式为YYYY-MM-DD HH:MM:SS）。
- **DEFAULT CURRENT_TIMESTAMP**: 默认值设置为当前时间戳。当插入新行时，如果没有为该列指定值，数据库会自动使用当前的日期和时间。

**示例**：在`users`表的`created_at`列上使用此设置，意味着每个新用户注册时，创建时间会自动记录。

## 4. `FOREIGN KEY` 的作用

- **外键**：用于建立两个表之间的关系。外键约束确保一个表中的值必须匹配另一个表中的主键值，从而维护数据的参照完整性。
- 语法：`FOREIGN KEY (当前表的列名) REFERENCES 引用表(引用表的列名)`
- 作用：防止插入无效数据，例如，确保`genealogies`表中的`created_by`列的值必须存在于`users`表的`user_id`列中。

**示例**：在`genealogies`表中，`FOREIGN KEY (created_by) REFERENCES users(user_id)`表示每个族谱的创建者必须是一个已存在的用户。

## 5. `TEXT` 的含义

- **TEXT**: 数据类型，用于存储可变长度的文本数据。与`VARCHAR`类似，但`TEXT`可以存储更长的文本（最大长度可达约65,535字符，取决于数据库设置）。
- 适用场景：适合存储较长的文本，如简介、描述等。

**示例**：在`members`表的`bio`列使用`TEXT`，允许存储成员的详细传记信息。

## 6. `FOREIGN KEY (member_id1) REFERENCES members(member_id)` 的语法讲解

- 这是外键约束的具体语法：
  - `FOREIGN KEY (member_id1)`：指定当前表（`marriages`）中的列`member_id1`作为外键。
  - `REFERENCES members(member_id)`：指定这个外键引用`members`表的`member_id`列（主键）。
- 作用：确保`marriages`表中的`member_id1`值必须存在于`members`表的`member_id`列中，从而保证婚姻关系中的成员是有效的。

## 7. `UNIQUE KEY unique_collab (user_id, genealogy_id)` 的语法讲解

- **UNIQUE KEY**: 定义一个唯一约束。
- **unique_collab**: 约束的名称（可选，但建议命名以便管理）。
- **(user_id, genealogy_id)**: 指定这两列的组合必须是唯一的。这意味着同一个用户和同一个族谱的组合不能重复，但单个列的值可以重复。

**示例**：在`collaborations`表中，这确保了同一个用户对同一个族谱只有一条协作记录，避免了重复邀请。

---

*笔记创建时间：2026年5月7日*

## 8. MySQL `SOURCE` 命令中的反斜杠转义问题

- **问题描述**：在 MySQL 命令行中执行 `SOURCE D:\little project\genecloud\schema.sql;` 时，报错 `Unknown command '\l'`。
- **原因分析**：`\` 在 MySQL 命令行中是**转义符号**，类似于编程语言中的转义字符。`\l` 会被 MySQL 解析为一个转义序列，而 `\l` 不是有效的转义序列，因此 MySQL 将其视为一个内置命令，但找不到该命令，所以报错。
- **正确用法**：在 MySQL `source` 命令中，路径应使用**正斜杠 `/`**，而不是反斜杠 `\`。
- **解决方案**：
  1. 在 MySQL 命令行中使用：`SOURCE d:/little project/genecloud/schema.sql;`
  2. 或在 PowerShell 中使用管道符：`Get-Content "d:\little project\genecloud\schema.sql" | mysql -u root -p genealogy_db`

**示例**：
```sql
-- 错误写法（反斜杠导致转义问题）：
SOURCE D:\little project\genecloud\schema.sql;

-- 正确写法（使用正斜杠）：
SOURCE d:/little project/genecloud/schema.sql;
```

**补充说明**：
- 这个问题仅出现在 Windows 的 MySQL 命令行客户端中，因为 Windows 默认使用反斜杠 `\` 作为路径分隔符，而 MySQL 将其视为转义字符。
- 在 PowerShell 或命令提示符中，可以使用反斜杠，但需要正确处理（如使用引号或转义）。
