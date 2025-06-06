# 通用Excel智能查询工具 (General Excel Smart Query Tool)

本项目是一个前后端分离的Web应用程序，允许用户上传Excel文件，然后使用自然语言查询与大型语言模型（LLM）交互来筛选和分析数据。

## 项目特点

*   **自然语言查询**: 用户可以使用日常语言提出数据查询请求。
*   **LLM集成**: 支持通过API（如硅基流动 SiliconFlow）或本地运行的Ollama与大模型交互，将自然语言转换为结构化查询条件。
*   **Excel文件处理**: 支持上传一个或多个 `.xls` 或 `.xlsx` 文件，并能处理多工作表（Sheet）数据。
*   **动态筛选**: 根据LLM解析的条件动态筛选Pandas DataFrame。
*   **结果展示与下载**: 在网页上以表格形式展示查询结果，并提供下载结果为Excel文件的功能。
*   **用户认证**: 基于JWT的用户注册和登录系统。
*   **可配置LLM**: 用户可以通过UI配置使用的LLM API类型、模型、端点和参数。

## 技术栈

*   **前端 (Frontend)**:
    *   Vue 3 (Composition API, `<script setup>`)
    *   Vite (构建工具)
    *   Axios (HTTP客户端)
    *   jwt-decode (JWT解析)
    *   HTML, CSS, JavaScript
*   **后端 (Backend)**:
    *   Python 3.x
    *   FastAPI (Web框架)
    *   Uvicorn (ASGI服务器)
    *   SQLModel (ORM, Pydantic数据验证)
    *   MySQL (用户认证数据库)
    *   Pandas (数据处理)
    *   Openpyxl (Excel文件读写)
    *   python-jose[cryptography] (JWT处理)
    *   Passlib[bcrypt] (密码哈希)
    *   python-dotenv (环境变量管理)
    *   Requests (调用外部LLM API)
    *   python-multipart (文件上传)
*   **LLM (可选)**:
    *   SiliconFlow API
    *   Ollama (本地运行模型如 Llama 3, Qwen, etc.)

## 项目结构
excel-query-agent/
├── backend/  ├── 后端/
│ ├── app/ # FastAPI应用核心代码
│ │ ├── core/ # 配置、安全等
│ │ ├── crud.py # 数据库操作
│ │ ├── database.py # 数据库模型和连接
│ │ ├── excel_processing.py # Excel和LLM处理逻辑
│ │ ├── excel_processing.py # Excel 和 LLM 处理逻辑
│ │ ├── main.py # FastAPI应用和路由
│ │ └── models.py # Pydantic数据模型
│ │ └── models.py # Pydantic 数据模型
│ ├── .env # 环境变量 (需自行创建)
│ └── requirements.txt # Python依赖
│ └── requirements.txt # Python 依赖
│
└── frontend/  └── 前端/
├── public/  ├── 公众号 /
├── src/  ├── 来源/
│ ├── assets/  │ ├── 资产 /
│ ├── components/ # Vue组件 (LoginForm, RegistrationForm, ExcelQueryTool)
│ ├── components/ # Vue 组件 （LoginForm， RegistrationForm， ExcelQueryTool）
│ ├── App.vue  │ ├── App.vue 软件官网
│ └── main.js
├── index.html
├── package.json # Node.js依赖
├── package.json # Node.js 依赖
└── vite.config.js

## 环境准备

### 后端 (Backend)

1.  **Python**: 确保已安装 Python 3.8 或更高版本。
2.  **MySQL数据库**:
    *   安装MySQL服务器。
    *   创建一个数据库，例如 `my_app_db` (与 `.env` 文件中的配置对应)。
3.  **Ollama (可选)**: 如果希望使用本地LLM，请安装并运行Ollama，并下载所需模型 (例如 `ollama pull llama3`)。

### 前端 (Frontend)

1.  **Node.js 和 npm/yarn**: 确保已安装 Node.js (推荐LTS版本) 和 npm (通常随Node.js安装) 或 yarn。

## 安装与启动

### 1. 后端 (FastAPI)

```bash
# 进入后端目录
cd backend

# (推荐) 创建并激活Python虚拟环境
python -m venv venv
# Windows:
# venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 创建 .env 文件
# 在 `backend/` 目录下创建一个名为 `.env` 的文件。
# 复制以下内容并根据您的环境修改MySQL连接信息和API密钥。
# 示例 .env 文件内容:
# DATABASE_URL="mysql+pymysql://YOUR_MYSQL_USER:YOUR_MYSQL_PASSWORD@YOUR_MYSQL_HOST:3306/my_app_db"
# SECRET_KEY="a_very_strong_and_unique_secret_key_for_jwt_generation_and_validation"
# ALGORITHM="HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES=60
# SILICONFLOW_API_KEY="sk-your_siliconflow_api_key_here" # 如果使用硅基流动

# 启动FastAPI应用 (开发模式)
# Uvicorn将运行在 http://localhost:8000
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

注意: create_db_and_tables() 会在应用启动时尝试创建用户表 (app_users)。请确保数据库已创建且连接字符串正确。
SILICONFLOW_API_KEY 在 excel_processing.py 中通过 settings.SILICONFLOW_API_KEY 读取，因此需要在 .env 和 config.py 中配置才能生效。

2.  **MySQL数据库**:
    *   **安装MySQL服务器**:
        *   **Windows**: 下载 MySQL Installer for Windows ([MySQL Community Downloads](https://dev.mysql.com/downloads/installer/))。在安装过程中，选择 "Server only" 或 "Developer Default" (包含服务器和工具)。记下您设置的 `root` 用户密码。
        *   **macOS**: 可以使用 Homebrew (`brew install mysql`) 或下载官方 DMG 安装包 ([MySQL Community Downloads](https://dev.mysql.com/downloads/mysql/))。
        *   **Linux (Ubuntu/Debian示例)**:
            ```bash
            sudo apt update
            sudo apt install mysql-server
            sudo mysql_secure_installation # 推荐运行此脚本进行安全配置
            ```
        *   **Docker (推荐用于快速开发和一致性环境)**:
            ```bash
            docker run --name some-mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=yourstrongpassword -d mysql:latest
            ```
            将 `yourstrongpassword` 替换为您自己的密码。
    *   **验证MySQL服务**: 确保MySQL服务正在运行。
    *   **创建数据库用户 (推荐)**: 为了安全起见，最好不要直接使用 `root` 用户连接应用。可以创建一个专门的用户：
        1.  连接到MySQL服务器 (使用root用户或具有创建用户权限的用户)：
            ```bash
            # 如果在本地安装
            mysql -u root -p
            ```
            或者使用MySQL Workbench等GUI工具。
        2.  创建新用户和数据库 (将 `myappuser`, `yourpassword`, `my_app_db` 替换为您选择的值)：
            ```sql
            CREATE DATABASE my_app_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            CREATE USER 'myappuser'@'localhost' IDENTIFIED BY 'yourpassword';
            GRANT ALL PRIVILEGES ON my_app_db.* TO 'myappuser'@'localhost';
            FLUSH PRIVILEGES;
            EXIT;
            ```
            如果您的FastAPI应用和MySQL不在同一台机器上，将 `'localhost'` 替换为FastAPI服务器的IP地址或 `'%'` (允许任何主机，但安全性较低)。
    *   **数据库名称**: 确保创建的数据库名称 (例如 `my_app_db`) 与您将在后端 `.env` 文件中 `DATABASE_URL` 配置的名称一致。


3. 前端 (Vue)
# 进入前端目录
cd frontend

# 安装Node.js依赖
npm install
# 或者使用yarn:
# yarn install

# 创建 .env 文件 (可选, 用于 VITE_API_BASE_URL)
# 在 `frontend/` 目录下创建一个名为 `.env` 的文件。
# 如果您的FastAPI后端运行在其他地址或端口，或者您想配置Excel API的基础路径：
# VITE_API_BASE_URL=http://localhost:8000/api/v1/excel

# 启动Vue开发服务器
# 通常会运行在 http://localhost:5173
npm run dev
# 或者使用yarn:
# yarn dev
使用说明
访问前端: 在浏览器中打开Vue开发服务器的地址 (通常是 http://localhost:5173)。
注册/登录: 创建一个账户或使用现有账户登录。
主页面 (Excel查询工具):
登录成功后，您将被导向Excel查询工具页面。
(可选) 配置LLM: 点击 "显示配置选项" 按钮，选择您希望使用的LLM服务（硅基流动或本地Ollama），并填写必要的API密钥、端点和模型参数。点击 "保存配置"。
上传文件: 点击 "选择文件" 上传一个或多个Excel文件 (.xls, .xlsx)，然后点击 "上传并处理文件"。系统会显示可用列名。
自然语言查询: 在输入框中输入您的查询请求，例如 "查找销售额大于1000且客户评级为A的记录"。
执行查询: 点击 "执行查询"。系统将使用配置的LLM解析您的查询，筛选数据并在下方表格中显示结果。LLM解析的条件也会显示出来。
下载结果: 如果查询有结果，可以点击 "下载结果" 按钮将筛选后的数据下载为Excel文件。
注意事项
安全性:
SECRET_KEY 用于JWT签名，务必使用强大且唯一的密钥，并妥善保管，尤其是在生产环境中。
API密钥（如 SILICONFLOW_API_KEY）也应保密。
LLM 提示词 (Prompts): excel_processing.py 中的系统提示词和用户提示词模板对LLM的解析能力至关重要。您可以根据需要进行调整和优化。
数据存储: 当前版本的 excel_processing.py 使用Python字典在内存中存储上传的Excel数据 (_MERGED_DATA_STORE 等)。这意味着数据会在服务器重启后丢失，并且不适合多用户并发使用。对于生产环境，应考虑使用更持久和可扩展的存储方案（如Redis缓存、临时文件存储，或针对每个用户/会话进行隔离）。
错误处理: 已包含基本的错误处理，但可以根据需要进一步增强。
.env 文件: 切勿将包含敏感密钥的 .env 文件提交到公共版本控制系统 (如GitHub)。 请将其添加到 .gitignore 文件中。
未来可能的增强
用户会话隔离，支持多用户同时使用独立的数据。
更高级的Excel数据类型处理和验证。
支持更复杂的查询逻辑和数据聚合。
集成Alembic进行数据库迁移。
前端UI/UX改进。
单元测试和集成测试。
请根据您的实际项目情况调整此README文件。
**关键点解释:**

*   **`.env` 文件:** 强调了创建 `.env` 文件的重要性，并给出了后端和前端的示例。这是存放敏感信息和环境特定配置的最佳实践。
*   **`SILICONFLOW_API_KEY` 配置:** 我在后端 `.env` 示例中添加了 `SILICONFLOW_API_KEY`，并在 `excel_processing.py` 中提到了它会通过 `settings.SILICONFLOW_API_KEY` 读取。你需要确保在 `backend/app/core/config.py` 中也添加这个字段：
    ```python
    # backend/app/core/config.py
    class Settings(BaseSettings):
        DATABASE_URL: str = os.getenv("DATABASE_URL", "")
        SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key")
        ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
        ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
        SILICONFLOW_API_KEY: Optional[str] = os.getenv("SILICONFLOW_API_KEY") # 添加此行

        class Config:
            env_file = ".env"
            # ...
    ```
*   **启动命令:** 清晰列出了前后端的启动步骤。
*   **使用说明:** 简要介绍了如何与应用交互。
*   **注意事项:** 涵盖了安全、数据存储和提示词等重要方面。