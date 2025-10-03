# 环境变量设置指南

## 安全警告 ⚠️

**永远不要在代码中硬编码API密钥！** 这会导致密钥泄露并被恶意使用。

## 设置步骤

### 1. 创建 .env 文件

在项目根目录创建 `.env` 文件：

```bash
touch .env
```

### 2. 添加API密钥

在 `.env` 文件中添加你的OpenAI API密钥：

```
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

### 3. 设置环境变量（可选）

你也可以直接在终端中设置环境变量：

```bash
# macOS/Linux
export OPENAI_API_KEY="sk-proj-your-actual-api-key-here"

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-proj-your-actual-api-key-here"

# Windows (Command Prompt)
set OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

### 4. 验证设置

运行应用程序，如果没有错误信息，说明环境变量设置成功。

## 重要提醒

1. **`.env` 文件已经被添加到 `.gitignore`**，不会被提交到Git仓库
2. **不要将 `.env` 文件分享给任何人**
3. **如果API密钥泄露，立即在OpenAI Dashboard重新生成**
4. **定期轮换API密钥以提高安全性**

## 故障排除

如果遇到 "OPENAI_API_KEY 环境变量未设置" 错误：

1. 检查 `.env` 文件是否存在
2. 确认API密钥格式正确
3. 重启应用程序
4. 检查是否有拼写错误

## 生产环境

在生产环境中，建议使用更安全的方式管理密钥：

- 使用密钥管理服务（如AWS Secrets Manager、Azure Key Vault）
- 使用容器编排工具的环境变量管理
- 使用CI/CD流水线的安全变量
