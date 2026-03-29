# IP 主题资源说明

这个目录只用于存放前端页面所需的主题视觉资源。  
不要把角色头像、角色立绘这类后端角色资源放到这里。

## 前端与后端资源分工

### 前端主题资源

放在 `AnimeSpeechGen/src/assets/ip-themes`：

- 首页首屏轮播图
- 首页 Logo、标题锁定图
- 首页第二屏主题入口大卡背景图
- 语音工坊舞台背景
- 装饰纹样、边框、名牌、光效、粒子
- 可复用纹理和 UI 遮罩

### 后端角色资源

放在 `AniVoiceBackend/static`：

- 角色头像
  - `AniVoiceBackend/static/character_avator/<Belong>/`
- 角色立绘
  - `AniVoiceBackend/static/stands/<Belong>/`
- 所有需要由角色接口返回给前端的角色资源

这与当前后端角色清单和静态资源逻辑保持一致，日常新增角色无需改动前端主题资源目录。

## 目录职责说明

### `shared`

- `shared/textures`
  - 公共纹理资源，例如纸纹、星尘、雾感噪点、闪光叠层。
  - 推荐格式：`webp` 或透明 `png`
  - 推荐规格：无缝纹理 `1024x1024`，全屏叠层 `1920x1080`

- `shared/ui`
  - 公共 UI 装饰资源，例如边框、遮罩、丝带、发光边片。
  - 推荐格式：透明 `png` 或 `svg`
  - 推荐长边：`512px` 到 `2048px`

### `genshin/home`

- `genshin/home/carousel`
  - 首页首屏轮播图
  - 用于推荐 IP、本周新增、热门推荐等首屏轮播内容
  - 推荐格式：`webp` 优先，`jpg/png` 可接受
  - 推荐规格：桌面端 `1920x1080`，最低 `1600x900`
  - 安全区域：主体尽量放在中间 `70%` 宽度和中间 `70%` 高度内

- `genshin/home/logos`
  - 首页 Logo、活动 Logo、标题锁定图
  - 推荐格式：透明 `png` 或 `svg`
  - 推荐宽度：`600px` 到 `1200px`

- `genshin/home/feature-cards`
  - 首页第二屏主题入口大卡背景图
  - 只服务首页第二屏，不再与语音工坊背景混用
  - 推荐格式：`webp`、`jpg`、`png`
  - 推荐规格：`1600x900` 或更高

### `genshin/voice`

- `genshin/voice/backgrounds`
  - 语音工坊页面舞台背景图
  - 仅服务语音工坊，不再承担首页入口图职责
  - 推荐格式：`webp` 或 `jpg/png`
  - 推荐规格：`1920x1080`，最低 `1600x900`

- `genshin/voice/ornaments`
  - 装饰叠层，例如元素纹章、边框角饰、名牌底板
  - 推荐格式：透明 `png` 或 `svg`
  - 推荐长边：`512px` 到 `1600px`

- `genshin/voice/effects`
  - 光效、雾层、粒子、泛光、波纹等舞台特效
  - 推荐格式：透明 `png`
  - 推荐规格：常见尺寸 `512x512`、`1024x1024`、`1920x1080`

### `starrail/home`

- `starrail/home/carousel`
  - 首页首屏轮播图目录
  - 当前可先留空，后续补真实素材

- `starrail/home/logos`
  - 星穹铁道首页 Logo 或标题图

- `starrail/home/feature-cards`
  - 首页第二屏主题入口大卡背景图
  - 当前建议将真实入口背景图放到这里
  - 该目录下可以先放占位图，后续再替换成正式素材

### `starrail/voice`

- `starrail/voice/backgrounds`
  - 语音工坊舞台背景图目录

- `starrail/voice/ornaments`
  - 工坊装饰纹样目录

- `starrail/voice/effects`
  - 工坊特效资源目录

## 资源映射建议

首页第二屏的主题入口大卡背景图，建议统一通过单独的资源映射文件管理，而不是在首页配置里直接散落导入图片。

建议使用：

- `src/config/ipHomeAssets.ts`

由该文件统一映射：

- `logo`
- `featureCardCover`

这样可以避免：

- 不同 IP 误用同一张图
- 文件名承担过多业务语义
- 首页内容配置和资源配置耦合过深

## 后端角色资源建议规格

这些资源不放在本目录，但建议继续遵循当前角色链路的尺寸标准。

- `AniVoiceBackend/static/character_avator/GenShin`
  - 正方形 `png/webp`
  - 推荐 `512x512`
  - 最低 `256x256`

- `AniVoiceBackend/static/stands/GenShin`
  - 透明背景 `png/webp`
  - 推荐长边 `1800px` 到 `2600px`
  - 最低 `1400px`

## 命名建议

- 前端主题资源推荐使用小写 `kebab-case`
- 后端角色资源推荐使用稳定角色键名，确保头像和立绘一一对应

示例：

- 前端：`genshin-home-feature-main.png`
- 前端：`starrail-home-feature-placeholder.svg`
- 前端：`genshin-logo.jpg`
- 后端：`Ayaka.png`
- 后端：`YaeMiko.png`

## 首批素材建议

### 前端

- `genshin/home/carousel`
  - 2 到 3 张首页首屏轮播图

- `genshin/home/logos`
  - 1 个原神首页 Logo

- `genshin/home/feature-cards`
  - 1 到 2 张首页第二屏入口图

- `genshin/voice/backgrounds`
  - 1 张语音工坊主舞台背景

- `genshin/voice/ornaments`
  - 2 到 4 张装饰叠层

- `starrail/home/feature-cards`
  - 1 张首页第二屏入口图

### 后端

- `static/character_avator/GenShin`
  - 6 到 8 个角色头像

- `static/stands/GenShin`
  - 6 到 8 张与头像一一对应的角色立绘

## 注意事项

- 大尺寸前端位图优先使用 `webp`，降低打包体积
- 透明叠层和特效优先使用透明 `png`
- 首页第二屏入口图不要再放进 `voice/backgrounds`
- 后端 `stands` 和 `character_avator` 目录里不要混放 Banner、装饰图或首页素材
