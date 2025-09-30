# 数据库迁移操作指南

本文档详细说明Flask应用的数据库迁移操作流程，包括迁移、回滚、状态检查等操作。

## 目录结构

```
migrations/
├── README.md          # 本文档
├── alembic.ini        # Alembic配置文件
├── env.py             # 迁移环境配置
├── script.py.mako     # 迁移脚本模板
└── versions/          # 迁移脚本目录
    ├── 2472b4e8b68e_initial_migration.py
    └── 44e3cc49892c_add_visit_count_field.py
```

## 迁移操作命令

### 1. 生成迁移脚本

当修改数据模型后，需要生成迁移脚本：

```bash
cd backend
set FLASK_APP=main.py
uv run flask db migrate -m "迁移描述"
```

**示例：**
```bash
uv run flask db migrate -m "add user email field"
```

### 2. 应用迁移

**手动应用迁移：**
```bash
uv run flask db upgrade
```

**自动应用迁移：**
应用启动时会自动执行迁移（已在main.py中实现）

### 3. 查看迁移状态

**查看当前迁移版本：**
```bash
uv run flask db current
```

**查看迁移历史：**
```bash
uv run flask db history
```

**查看详细迁移信息：**
```bash
uv run flask db history --verbose
```

### 4. 回滚迁移

**回滚到上一个版本：**
```bash
uv run flask db downgrade
```

**回滚到特定版本：**
```bash
uv run flask db downgrade <revision_id>
```

**示例：**
```bash
uv run flask db downgrade 2472b4e8b68e
```

## 完整工作流程

### 开发环境

1. **修改数据模型** - 编辑 `app/models.py`
2. **生成迁移脚本** - `uv run flask db migrate -m "描述"`
3. **检查生成的脚本** - 查看 `migrations/versions/` 中的文件
4. **应用迁移** - `uv run flask db upgrade`
5. **测试验证** - 确保功能正常

### 生产环境部署

1. **备份数据库** - 确保数据安全
2. **应用迁移** - 应用启动时自动执行
3. **验证功能** - 确认应用正常运行
4. **监控日志** - 检查迁移是否成功

## 特殊情况处理

### 首次运行

如果是首次运行或迁移表不存在，应用会自动初始化数据库：

```python
# 自动回退逻辑（已在main.py中实现）
db.create_all()  # 创建所有表结构
```

### 迁移冲突解决

如果遇到迁移冲突：

1. **检查当前状态**：
   ```bash
   uv run flask db current
   uv run flask db history
   ```

2. **回滚到稳定版本**：
   ```bash
   uv run flask db downgrade <stable_revision>
   ```

3. **重新生成和应用迁移**：
   ```bash
   uv run flask db migrate -m "fix migration conflict"
   uv run flask db upgrade
   ```

### 数据迁移

对于需要数据迁移的情况：

1. **在迁移脚本中添加数据操作**：
   ```python
   def upgrade():
       # 模式变更
       op.add_column('user_visits', sa.Column('visit_count', sa.Integer(), nullable=False))
       
       # 数据迁移
       op.execute("UPDATE user_visits SET visit_count = 1 WHERE visit_count IS NULL")
   ```

2. **确保回滚操作正确**：
   ```python
   def downgrade():
       op.drop_column('user_visits', 'visit_count')
   ```

## 最佳实践

### 1. 迁移文件管理

- 每次变更生成一个迁移文件
- 使用清晰的迁移描述
- 迁移文件纳入版本控制
- 不要手动修改已提交的迁移文件

### 2. 开发规范

- 在开发分支进行模型变更
- 先本地测试迁移再提交
- 确保迁移脚本可回滚
- 为生产环境的数据迁移准备回滚方案

### 3. 部署策略

- 生产环境部署前在测试环境验证迁移
- 重要数据变更前进行备份
- 监控迁移过程中的性能影响
- 准备回滚计划

## 常见问题

### Q: 迁移失败怎么办？
A: 检查错误信息，通常是因为：
- 数据库连接问题
- 迁移脚本语法错误
- 数据约束冲突

### Q: 如何重置数据库？
A: 删除数据库文件，重新初始化：
```bash
# 删除数据库文件
rm app.db

# 重新初始化
uv run flask db upgrade
```

### Q: 迁移文件冲突怎么解决？
A: 协调团队成员，确保迁移顺序一致，必要时手动调整迁移依赖。

## 相关文件说明

- **alembic.ini** - 数据库连接配置
- **env.py** - 迁移环境配置，包含应用上下文设置
- **script.py.mako** - 迁移脚本模板

## 紧急联系方式

如遇生产环境迁移问题，请联系系统管理员。

---

*最后更新: 2025-09-30*
*文档版本: 1.0*