# Git大文件问题解决方案

## 🎯 推荐解决方案：使用 git filter-repo

### 为什么选择 git filter-repo？
- ✅ **最安全**: 专门设计用于重写Git历史
- ✅ **最快速**: 比 git filter-branch 快10-50倍
- ✅ **最可靠**: 更少的边缘情况和错误
- ✅ **官方推荐**: Git官方推荐替代 git filter-branch

## 📋 解决步骤

### 步骤1: 备份当前工作
```bash
# 1. 确保所有工作已提交
git status

# 2. 创建备份分支
git branch backup-before-cleanup

# 3. 备份整个项目文件夹
cp -r omega-update omega-update-backup
```

### 步骤2: 安装 git filter-repo
```bash
# 方法1: 使用pip安装
pip install git-filter-repo

# 方法2: 下载单文件版本
curl -O https://raw.githubusercontent.com/newren/git-filter-repo/main/git-filter-repo
chmod +x git-filter-repo
sudo mv git-filter-repo /usr/local/bin/
```

### 步骤3: 查找大文件位置
```bash
# 查找历史中的大文件
git rev-list --objects --all | grep "$(git verify-pack -v .git/objects/pack/*.idx | sort -k 3 -nr | head -10 | awk '{print$1}')"

# 或者使用更简单的方法查找特定文件
git log --all --full-history -- test_1gb_file.zip
```

### 步骤4: 移除大文件
```bash
# 从整个Git历史中移除指定文件
git filter-repo --path test_1gb_file.zip --invert-paths

# 如果有多个大文件，可以使用
git filter-repo --path test_1gb_file.zip --path other_large_file.zip --invert-paths
```

### 步骤5: 清理和验证
```bash
# 强制垃圾回收
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 检查仓库大小
du -sh .git

# 验证大文件已被移除
git log --all --full-history -- test_1gb_file.zip
```

### 步骤6: 重新添加远程仓库
```bash
# filter-repo会移除所有远程仓库，需要重新添加
git remote add origin <your-github-repo-url>

# 强制推送（注意：这会重写远程历史）
git push --force-with-lease origin main
```

## ⚠️ 风险评估和注意事项

### 高风险操作
- **重写历史**: 会改变所有提交的SHA值
- **强制推送**: 会覆盖远程仓库历史
- **协作影响**: 其他开发者需要重新克隆仓库

### 安全措施
1. **完整备份**: 操作前备份整个项目
2. **分支保护**: 创建备份分支
3. **验证测试**: 操作后验证功能完整性
4. **团队通知**: 如有协作者，需要提前通知

## 🔄 替代方案

### 方案A: 使用 git filter-branch (不推荐)
```bash
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch test_1gb_file.zip' \
--prune-empty --tag-name-filter cat -- --all
```

### 方案B: 创建新仓库 (最安全但工作量大)
```bash
# 1. 创建新的空仓库
git init omega-update-clean
cd omega-update-clean

# 2. 复制当前工作目录的文件（不包括.git）
cp -r ../omega-update/* .
cp -r ../omega-update/.* . 2>/dev/null || true

# 3. 重新初始化Git历史
git add .
git commit -m "Initial commit with clean history"
```

### 方案C: 使用 Git LFS (适用于需要保留大文件的情况)
```bash
# 安装Git LFS
git lfs install

# 追踪大文件类型
git lfs track "*.zip"

# 添加.gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

## 🚀 推荐执行流程

### 对于Omega更新服务器项目：
1. **使用方案1 (git filter-repo)** - 最佳平衡
2. **保留模块化重构成果** - 确保不丢失已完成工作
3. **验证功能完整性** - 重构后的工具正常运行
4. **更新文档** - 反映清理后的仓库状态

## 📝 操作后检查清单

- [ ] 大文件已从历史中完全移除
- [ ] 仓库大小显著减小
- [ ] 模块化重构的所有文件都存在
- [ ] 启动脚本正常工作
- [ ] 配置文件完整
- [ ] 文档更新完整
- [ ] 可以成功推送到GitHub

## 🔧 故障排除

### 如果 git filter-repo 不可用：
```bash
# 使用Docker运行
docker run --rm -v $(pwd):/repo -w /repo python:3.9 \
bash -c "pip install git-filter-repo && git filter-repo --path test_1gb_file.zip --invert-paths"
```

### 如果推送仍然失败：
```bash
# 检查是否还有其他大文件
find .git/objects/pack/ -name "*.idx" -exec git verify-pack -v {} \; | \
sort -k 3 -nr | head -10

# 检查当前分支大小
git count-objects -vH
```

### 如果需要恢复：
```bash
# 从备份分支恢复
git checkout backup-before-cleanup
git branch -D main
git checkout -b main
```
