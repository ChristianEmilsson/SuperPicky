---
description: PyInstaller 打包、签名、公证完整流程 - macOS App Distribution
---

# SuperPicky macOS 打包、签名、公证流程

## 前置条件

- Developer ID Application 证书已安装在 Keychain
- 已配置 notarytool profile: `notarytool-profile`
- Apple ID: `james@jamesphotography.com.au`
- Team ID: `JWR6FDB52H`

## 1. 确保依赖安装正确

PyInstaller 使用系统 Python，需要确保依赖安装在用户 site-packages：

```bash
# 检查 PySide6 是否安装
python3 -c "import PySide6; print(PySide6.__path__[0])"

# 如果未安装，安装到用户 site-packages
pip3 install --user PySide6
```

## 2. 清理并构建

```bash
# // turbo
cd /Users/jameszhenyu/Documents/JamesAPPS/SuperPicky2026
rm -rf build dist
pyinstaller SuperPicky.spec --noconfirm
```

构建完成后检查：`dist/SuperPicky.app` 应该存在

## 3. 代码签名

使用 Developer ID Application 证书签名：

```bash
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: James Zhen Yu (JWR6FDB52H)" \
  --options runtime \
  dist/SuperPicky.app
```

验证签名：
```bash
# // turbo
codesign --verify --verbose dist/SuperPicky.app
```

## 4. 创建 ZIP 并提交公证

公证需要 ZIP 格式：

```bash
cd dist
rm -f SuperPicky.zip
ditto -c -k --keepParent SuperPicky.app SuperPicky.zip
ls -lh SuperPicky.zip
```

提交公证（等待完成）：
```bash
xcrun notarytool submit SuperPicky.zip \
  --apple-id "james@jamesphotography.com.au" \
  --team-id "JWR6FDB52H" \
  --keychain-profile "notarytool-profile" \
  --wait
```

## 5. Staple 公证票据

公证成功后，将票据附加到 app：

```bash
xcrun stapler staple dist/SuperPicky.app
xcrun stapler validate dist/SuperPicky.app
```

## 6. 创建 DMG 发布包

使用 `hdiutil` 创建 DMG 磁盘映像：

```bash
cd dist

# 确定架构类型
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
  ARCH_NAME="arm64"  # Apple Silicon (M1/M2/M3)
else
  ARCH_NAME="x64"    # Intel
fi

# 删除旧的 DMG
rm -f 慧眼选鸟v3.9_${ARCH_NAME}.dmg

# 创建临时目录并复制 app
mkdir -p dmg_temp
cp -R SuperPicky.app dmg_temp/
ln -s /Applications dmg_temp/Applications

# 创建 DMG（包含 Applications 快捷方式）
hdiutil create -volname "慧眼选鸟 V3.9" \
  -srcfolder dmg_temp \
  -ov -format UDZO \
  慧眼选鸟v3.9_${ARCH_NAME}.dmg

# 清理临时目录
rm -rf dmg_temp

# 验证 DMG
ls -lh 慧眼选鸟v3.9_${ARCH_NAME}.dmg
```

发布文件位置：
- Apple Silicon: `/Users/jameszhenyu/Documents/JamesAPPS/SuperPicky2026/dist/慧眼选鸟v3.9_arm64.dmg`
- Intel: `/Users/jameszhenyu/Documents/JamesAPPS/SuperPicky2026/dist/慧眼选鸟v3.9_x64.dmg`

---

## 常见问题

### 问题 1: ModuleNotFoundError: No module named 'PySide6'

**原因**: PyInstaller 使用系统 Python，但 PySide6 只安装在虚拟环境中

**解决**: 
```bash
pip3 install --user PySide6
```

### 问题 2: exiftool not found

**原因**: 打包后的代码使用 `sys._MEIPASS` 查找 bundled 资源，但代码中没有正确检查

**解决**: 在使用 exiftool 的模块中添加：
```python
import sys
import os

def _find_exiftool():
    # 优先检查 PyInstaller 打包环境
    if hasattr(sys, '_MEIPASS'):
        bundled = os.path.join(sys._MEIPASS, 'exiftool_bundle', 'exiftool')
        if os.path.exists(bundled):
            return bundled
    # 开发环境回退
    ...
```

### 问题 3: name 'sys' is not defined

**原因**: 添加了 `sys._MEIPASS` 检查但忘记导入 `sys` 模块

**解决**: 在文件开头添加 `import sys`

---

## 一键完整流程

```bash
cd /Users/jameszhenyu/Documents/JamesAPPS/SuperPicky2026

# 1. 清理并构建
rm -rf build dist && pyinstaller SuperPicky.spec --noconfirm

# 2. 签名
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: James Zhen Yu (JWR6FDB52H)" \
  --options runtime dist/SuperPicky.app

# 3. 创建 ZIP 并提交公证
cd dist && rm -f SuperPicky.zip && \
ditto -c -k --keepParent SuperPicky.app SuperPicky.zip && \
xcrun notarytool submit SuperPicky.zip \
  --apple-id "james@jamesphotography.com.au" \
  --team-id "JWR6FDB52H" \
  --keychain-profile "notarytool-profile" \
  --wait

# 4. Staple 票据
xcrun stapler staple SuperPicky.app

# 5. 创建 DMG 发布包（自动检测架构）
ARCH_NAME=$([ "$(uname -m)" = "arm64" ] && echo "arm64" || echo "x64") && \
rm -f 慧眼选鸟v3.9_${ARCH_NAME}.dmg && \
mkdir -p dmg_temp && \
cp -R SuperPicky.app dmg_temp/ && \
ln -s /Applications dmg_temp/Applications && \
hdiutil create -volname "慧眼选鸟 V3.9" \
  -srcfolder dmg_temp -ov -format UDZO \
  慧眼选鸟v3.9_${ARCH_NAME}.dmg && \
rm -rf dmg_temp && \
ls -lh 慧眼选鸟v3.9_${ARCH_NAME}.dmg
```

