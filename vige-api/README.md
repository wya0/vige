Install [`pipenv`](https://pipenv.readthedocs.io/en/latest/) with `pip install --user pipenv` or `brew install pipenv`.

```shell

cd vige/vige-api

# create virtual env & install dependencies
make install

# active venv
pipenv shell

# create local_config.py if it's not exists
# vige-api/vige/local_config.py
JWT_SECRET_KEY = 'jwt_secret_key'
JWT_COOKIE_SECURE = False
SECRET_KEY = 'secret_key'

# create db
createdb vige 

# migrate db
make upgrade-db


# initial testing user & role

# create role admin
python ./vige/cli.py bo_create_role -n admin

# create user admin
python ./vige/cli.py bo_create_user -n admin

# assign admin role to admin user
python ./vige/cli.py bo_set_role -u admin -r admin

# assign permissions for role admin
python ./vige/cli.py bo_set_perm -r admin -p all


# run in dev mode
make run

# run test
make test

```
Translations(Optionally)

-   init babel: `make babel-init LANG=zh`
-   mark translation strings with [gettext](https://docs.python.org/3/library/gettext.html#gettext) functions
-   extract translation strings: `make babel-update`
-   update translations and finally compile them for use: `make babel-compile`

---

### 数据库迁移（Alembic / Makefile 快捷命令）

当你在 `models.py` 中新增表或字段后，按以下步骤生成并应用迁移：

1）生成迁移（自动检测模型变更并生成脚本）

```bash
# 在 vige-api 目录下执行，双引号内填写你的变更说明
make db "add some tables"
```

2）升级数据库到最新版本

```bash
make upgrade-db
```

常用命令补充：

- 查看当前迁移版本（可用于排障）
  ```bash
  make config-db
  ```
- 如需更细粒度控制，可直接使用 Alembic 原生命令（需要激活 pipenv 或用 pipenv run）：
  ```bash
  # 示例：回滚一步
  pipenv run alembic downgrade -1
  ```

---

### Windows 使用说明（后端）

在 Windows 上建议优先使用 Docker Desktop 或 WSL2。若使用原生 Windows，请参考以下替代命令与注意事项。

1）安装依赖与启动

```powershell
cd vige\vige-api
pipenv install --dev
# 初始化数据库迁移（需已启动 Postgres/Redis）
pipenv run alembic upgrade head
# 启动 API
pipenv run uvicorn vige.app:app --reload --port 8000
# 启动任务队列（可选）
pipenv run huey_consumer -w 2 vige.huey_app.huey
```

2）依赖服务（Postgres/Redis）

- 推荐用 Docker 启动：
```bash
docker run -d --name vige-postgres -p 5432:5432 \
  -e POSTGRES_DB=vige -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres postgres:14
docker run -d --name vige-redis -p 6379:6379 redis:6
```

- `vige-api/vige/local_config.env` 示例：
```env
SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@localhost:5432/vige
REDIS_HOST=localhost
REDIS_PORT=6379
EXTERNAL_URL=http://127.0.0.1:8000
```

3）常见提示

- 如遇 `bash^M`，请确保脚本（如 `entrypoint.sh`）为 LF 换行。
- 个别 Python 包在 Windows 上可能需要构建工具（如 psycopg2、lxml、cryptography、pymupdf、soundfile）。若安装报错，建议改用 Docker/WSL2 或安装 Microsoft C++ Build Tools 后重试。
