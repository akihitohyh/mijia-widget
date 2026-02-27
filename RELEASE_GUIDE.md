# GitHub Releases 发布指南

## 发布包说明

### 源码包 (mijia-widget-v1.0.0.7z)
包含完整的项目源码和启动脚本，用户需要自行安装Python和依赖。

**包含内容：**
- 所有Python源码文件
- 启动脚本 (.bat, .vbs)
- README.md 使用说明
- requirements.txt 依赖列表

**不包含内容：**
- Git仓库文件 (.git)
- Python虚拟环境 (venv)
- 编译缓存 (__pycache__, build)
- 打包后的EXE文件（需要用户自行打包）

---

## 发布步骤

### 1. 登录GitHub
访问: https://github.com/akihitohyh/mijia-widget/releases

### 2. 创建新Release
点击 **"Draft a new release"** 按钮

### 3. 填写发布信息

**版本号 (Tag version):**
```
v1.0.0
```

**标题 (Release title):**
```
米家桌面插件 v1.0.0
```

**描述 (Description):**
```markdown
## 米家桌面插件 v1.0.0

Windows桌面小工具，实时显示米家设备状态和智能插座用电信息。

### 功能特性
- 自动同步米家账号设备
- 显示设备在线/离线状态
- 智能插座用电信息显示（功率、今日用电、累计用电）
- 点击穿透模式
- 系统托盘图标支持
- 图形化扫码登录
- 窗口置顶/调整大小

### 安装方式

#### 方式一：Python源码运行（推荐）
1. 安装Python 3.8+
2. 解压本压缩包
3. 安装依赖：`pip install -r requirements.txt`
4. 登录米家：`mijiaAPI --login`
5. 运行：`python main_widget.py`

#### 方式二：打包为EXE
运行 `build.bat` 自动生成EXE文件

### 系统要求
- Windows 10 / Windows 11
- Python 3.8+
- 米家账号

### 注意事项
- 首次使用需要先登录米家账号
- 详细使用说明请查看 README.md
```

### 4. 上传文件
点击 **"Attach binaries by dropping them here or selecting them"**

选择文件：`mijia-widget-v1.0.0.7z`

### 5. 发布
- 如果这是正式版本，勾选 **"This is a pre-release"** （预览版）
- 点击 **"Publish release"**

---

## 版本号规范

使用语义化版本号 (Semantic Versioning):

| 版本格式 | 说明 |
|---------|------|
| v1.0.0 | 主版本号.次版本号.修订号 |
| v1.0.1 | 修复bug |
| v1.1.0 | 新增功能 |
| v2.0.0 | 重大更新 |

---

## 文件清单

已生成的发布文件：
```
mijia-widget-v1.0.0.7z  (17KB)
```

---

## 发布完成后的分享链接

发布完成后，分享链接格式：
```
https://github.com/akihitohyh/mijia-widget/releases/tag/v1.0.0
```
