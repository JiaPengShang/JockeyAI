# OpenAI API 设置指南

## 问题描述
您遇到的错误表明OpenAI API密钥无效或已过期。

## 解决步骤

### 1. 获取新的API密钥
1. 访问 [OpenAI API Keys页面](https://platform.openai.com/account/api-keys)
2. 登录您的OpenAI账户
3. 点击"Create new secret key"创建新的API密钥
4. 复制新生成的API密钥（以`sk-`开头）

### 2. 设置API密钥

#### 方法一：直接修改配置文件（推荐用于测试）
编辑 `config.py` 文件，将第8行替换为您的实际API密钥：

```python
OPENAI_API_KEY = "sk-your-actual-api-key-here"
```

#### 方法二：使用环境变量（推荐用于生产环境）
1. 在项目根目录创建 `.env` 文件
2. 在文件中添加：
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. 验证设置
运行应用程序，如果设置正确，OCR功能应该能正常工作。

### 4. 常见问题
- **API密钥格式错误**：确保密钥以 `sk-` 开头
- **账户余额不足**：检查您的OpenAI账户余额
- **API配额用完**：等待配额重置或升级账户

### 5. 安全提醒
- 不要将API密钥提交到版本控制系统
- 定期轮换API密钥
- 在生产环境中使用环境变量存储敏感信息
