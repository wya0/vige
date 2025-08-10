## 贡献指南（精简版）

### 本地运行
- 后端：`cd vige-api && pipenv sync --dev && pipenv run uvicorn vige.app:app --reload`
- 前端：`cd vige-web && yarn && yarn dev`（BO/Wechat 同理）
- 数据库/缓存：可使用 `docker-compose up -d postgres redis`

### 提交规范
- 建议使用 Conventional Commits：`feat: ...`、`fix: ...`、`chore: ...`
- 新功能/修复需附最小验证说明（或截图）

### PR 流程
- 从 `master` 切分支；
- 保持 PR 小而清晰；
- 通过 CI（编译/导入检查）后由维护者合并。

### 代码规范要点
- 后端：Pydantic 2 语法（pattern、json_schema_extra）、统一错误响应、Session 隔离、ProfileMixin 两步法；
- 前端：避免 ES2020+ 语法（?.、??、import()），统一 axios 响应处理。

