# SpeechGenWeb

SpeechGenWeb 是一个面向二次元角色语音复现的 Web 项目，主要基于语音克隆技术，为特定 IP 下的角色提供语音生成能力。当前项目面向的典型场景包括《原神》、《崩坏：星穹铁道》等角色语音风格复现与试听展示。

项目整体由前后端两部分组成：

- `AnimeSpeechGen`：前端页面与交互逻辑
- `AniVoiceBackend`：后端接口、用户系统、资源管理与语音生成调度

## 项目目标

本项目的主要目标是：

- 为特定角色提供接近原角色风格的语音生成体验
- 提供基础的注册、登录、验证码、音频生成与静态资源访问能力
- 通过前后端分离的方式，方便本地部署、调试与后续扩展

## 技术栈

- 前端：Vue 3 + Vite
- 后端：FastAPI
- 数据库：PostgreSQL
- 缓存：Redis
- 语音生成：依赖 GPT-SoVITS 提供的 API 接口

## 特别说明

本项目的语音生成能力依赖：

- GPT-SoVITS 项目提供的推理 API 接口
- 基于 GPT-SoVITS 训练得到的模型权重文件

请务必对相关开源项目及其作者保持尊重。没有 GPT-SoVITS 项目及相关训练流程的支持，本项目无法完成实际的角色语音复现能力。

如果你在使用、修改或传播本项目，请同时遵守 GPT-SoVITS 及相关依赖项目自身的许可证、使用条款和社区规范。

## 目录结构

```text
SpeechGenWeb/
├─ AnimeSpeechGen/       # 前端工程
├─ AniVoiceBackend/      # 后端工程
├─ start-dev.bat         # 纯 bat 一键启动脚本
├─ start-dev.ps1         # PowerShell 一键启动脚本
└─ README.md
```

## 运行环境

建议环境：

- Windows
- Miniconda / Anaconda
- Conda 环境名：`web`
- Node.js / npm
- PostgreSQL
- Redis

后端当前默认通过以下方式启动：

```bash
conda run -n web python app_fast.py
```

## 快速启动

### 方式一：一键启动

如果本机环境已准备好，可以直接运行：

```bat
start-dev.bat
```

或使用 PowerShell：

```powershell
.\start-dev.ps1
```

启动脚本会尝试：

- 读取 `.env` 配置
- 启动 PostgreSQL
- 启动前端开发服务
- 启动 FastAPI 后端

### 方式二：分别启动前后端

前端：

```bash
cd AnimeSpeechGen
npm run dev
```

后端：

```bash
cd AniVoiceBackend
conda run -n web python app_fast.py
```

## 配置说明

后端支持通过 `AniVoiceBackend/.env` 配置运行参数，典型配置包括：

- `APP_HOST` / `APP_PORT`：当前后端服务自身地址
- `OLLAMA_HOST` / `OLLAMA_PORT`：远程 Ollama 服务地址
- `POSTGRES_*`：PostgreSQL 配置
- `REDIS_*`：Redis 配置
- `MAIL_*`：邮件服务配置
- `SOVITS_ADDR`：GPT-SoVITS 接口地址

可以参考：

```text
AniVoiceBackend/.env.example
```

## 使用边界

本项目仅面向学习、研究、技术验证与个人非商业交流用途。

使用本项目时，请自行确保：

- 不侵犯原作品、原角色、配音演员或相关权利人的合法权益
- 不将生成内容用于误导、冒充、诽谤、侵权或其他不当用途
- 不在未获授权的场景下公开传播敏感或高仿真语音内容

## 严禁商用

本项目严禁用于任何形式的商业用途。

包括但不限于：

- 直接售卖本项目代码、服务或部署版本
- 将生成语音用于收费产品、商业推广、广告投放或引流变现
- 将角色语音克隆能力封装后对外提供商业 API 或付费服务
- 在任何未经明确授权的商业化项目中使用本项目及其衍生成果

如果你有商业化需求，请先自行确认：

- 相关模型、数据、角色、声音、素材的权利归属
- 上游依赖项目的许可条件
- 目标使用场景下的法律、平台规范与授权要求

## 致谢

感谢 GPT-SoVITS 及相关社区项目提供的技术基础、接口能力与训练生态支持。

也感谢所有为角色语音复现、语音克隆、推理部署、前后端工程化做出贡献的开发者与研究者。
