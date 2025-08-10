### Vige（维格）

Vige（维格）是一个基于 FastAPI + Vue 的一体化工程模板，包含后端 API、前台 Web、后台管理与微信 H5 客户端，内置认证、任务队列、国际化、媒体上传与统一的 API 规范，适合作为中小型项目的起步框架。

English brief is provided at the end of this document.

---

### 特性（Features）

- 模块化 FastAPI 后端（users、media、settings、wechat 等）
- JWT + Cookie 认证与 CSRF 防护，统一前缀 `/v1`
- Redis + Huey 异步任务队列（环境可配置）
- PostgreSQL（SQLAlchemy 2.0）+ Alembic 数据迁移
- i18n（Babel），Makefile 常用脚本
- 媒体上传与静态挂载 `/media`
- 三套前端：Web（iView）、Admin（iView）、WeChat H5（Mint UI）
- 统一 axios 拦截器，响应结构 `{ success, data, message }`

---

### 技术栈（Tech Stack）

- 后端：FastAPI、SQLAlchemy 2.0、Alembic、Redis、Huey、Pydantic 2.x
- 前端（Web/Admin）：Vue 2、iView、Vue Router、Vuex、axios
- 前端（WeChat）：Vue 2、Mint UI、axios
- 工具：pipenv、yarn、Babel、Uvicorn

---

### 目录结构（Monorepo Structure）

```
vige/
  ├─ vige-api/        # FastAPI 后端
  ├─ vige-web/        # Web 客户端（Vue + iView）
  ├─ vige-bo/         # 管理后台（Vue + iView）
  └─ vige-wechat/     # 微信 H5 客户端（Vue + Mint UI）
```

关键后端文件：
- `vige-api/vige/app_factory.py`：应用创建、Redis 初始化、中间件、`/v1/ping`
- `vige-api/vige/api/__init__.py`：模块路由注册（users、settings、wechat、media 等）
- `vige-api/vige/config.py`：集中配置，支持 `local_config.env`
- `vige-api/Makefile`：安装、运行、迁移、测试、i18n 脚本

---

### 环境要求（Requirements）

- Python 3.10
- PostgreSQL 13+
- Redis 5+
- Node.js 14+ 与 yarn

---

### 快速开始（推荐）

使用 Makefile（后端 + 本地 env 自动生成）：

```bash
# 启动后端（首次会在 vige-api/vige/local_config.env 写入示例配置）
make api

# 可选：启动任务队列 Worker
make worker

# 前端开发（任选其一）
make web    # vige-web
make bo     # vige-bo
make wechat # vige-wechat
```

使用 Docker（数据库/缓存/后端一键起）：

```bash
docker-compose up -d postgres redis api
# API: http://localhost:8000
```

---

### 后端（vige-api）本地开发

1）安装依赖并进入虚拟环境

```bash
cd vige/vige-api
make install
pipenv shell
```

2）创建 `vige-api/vige/local_config.env`（覆盖 `vige/config.py` 默认值）

```env
ENV=local
DEBUG=true
SECRET_KEY=your_secret_key
AUTHJWT_SECRET_KEY=your_jwt_secret
AUTHJWT_COOKIE_SECURE=false
SQLALCHEMY_DATABASE_URI=postgresql://localhost/vige
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=10
EXTERNAL_URL=http://localhost:8000
UPLOADS_DEFAULT_DEST=./instance
```

3）初始化数据库并迁移

```bash
createdb vige
make upgrade-db
```

4）初始化后台管理员（可选，推荐）

```bash
make create-role
make create-user
make set-role
make set-perm
```

5）启动后端

```bash
make run
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

6）运行测试

```bash
make test
```

说明：
- 静态媒体目录挂载在 `/media`（物理目录 `vige-api/instance`）。
- 如需异步任务，另启 worker：`make worker`。

---

### 前端本地开发

前端默认通过代理将 API 请求转发至 `/v1`，可在各自的 `vue.config.js` 调整后端地址（默认 `http://localhost:8000`）。

Web（vige-web）

```bash
cd vige/vige-web
yarn install
yarn dev
# App: http://localhost:8080
```

Admin（vige-bo）

```bash
cd vige/vige-bo
yarn install
yarn dev
# App: http://localhost:8080 (or next free port)
```

WeChat H5（vige-wechat）

```bash
cd vige/vige-wechat
yarn install
yarn dev
# App: http://localhost:8080 (or next free port)
```

---

### Docker（后端）

构建并运行后端服务，请挂载本地配置：

```bash
cd vige/vige-api
docker build -t vige-api .

docker run --rm \
  -p 8000:8000 \
  -v $(pwd)/vige/local_config.env:/vige/vige/local_config.env \
  --name vige-api \
  vige-api web

# 可选：启动 worker
docker run --rm \
  -v $(pwd)/vige/local_config.env:/vige/vige/local_config.env \
  --name vige-worker \
  vige-api worker
```

容器需要能访问 PostgreSQL 与 Redis（通过 `local_config.env` 配置）。

---

### API 规范

- 基础路径：`/v1`
- 认证：JWT + Cookie（CSRF：`X-CSRF-TOKEN`）
- 成功响应：`{ "success": true, "data": ... }`
- 失败响应：`{ "success": false, "message": "..." }`（可包含 details）
- 文档：`http://localhost:8000/docs`

---

### 国际化（i18n）

后端使用 Babel，脚本已集成在 Makefile：

```bash
# 在 vige-api 目录
make babel-init LANG=zh
make babel-update
make babel-compile
```

---

### 开发注意事项

- 配置优先通过 `pydantic-settings` 读取 `vige-api/vige/local_config.env`
- 使用 Alembic 管理迁移（Makefile 提供常用命令）
- 前端 axios 拦截器已统一处理 `.data`、错误提示与 401/403 跳转
- 媒体上传统一走后端 `/media` 模块，静态对外挂载 `/media`

---

### 参与贡献（Contributing）

欢迎提交 Issue 与 Pull Request。请保持 PR 聚焦单一改动，并遵循项目结构（后端模块位于 `vige-api/vige/api/*`，各前端位于各自子项目内）。

本地提交前建议启用 pre-commit：

```bash
pip install pre-commit
pre-commit install
# 之后每次提交会自动执行基础检查（ruff/black/isort 等）
```

---

### 许可证（License）

本项目使用 MIT 许可证，详见根目录 `LICENSE` 文件。

---

### English Version (Brief)

Vige is a FastAPI + Vue monorepo boilerplate bundling an API backend, a web app, an admin console, and a WeChat H5 client. It includes JWT + Cookie auth with CSRF, Redis + Huey tasks, i18n, media uploads, and a consistent API response shape.

Features
- FastAPI (modular), `/v1` base path, `/v1/ping`
- JWT + Cookie auth, CSRF, Redis + Huey
- PostgreSQL (SQLAlchemy 2.0) + Alembic
- i18n (Babel), Makefile helpers
- Media upload static mount at `/media`
- Frontends: Web/Admin (Vue 2 + iView), WeChat H5 (Mint UI)

Quick Start
```bash
# Backend
cd vige/vige-api && make install && pipenv shell
createdb vige && make upgrade-db
make run  # http://localhost:8000, docs: /docs

# Frontend (example: web)
cd vige/vige-web && yarn install && yarn dev
```

License: MIT

