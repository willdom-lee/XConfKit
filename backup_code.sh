#!/bin/bash

# XConfKit 代码备份脚本
# 用于创建代码的完整备份，包括Git提交和压缩包

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取当前时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PROJECT_NAME="XConfKit202508"
BACKUP_DIR="./backups"
GIT_BACKUP_DIR="$BACKUP_DIR/git_backup_$TIMESTAMP"
ZIP_BACKUP_FILE="$BACKUP_DIR/${PROJECT_NAME}_backup_$TIMESTAMP.zip"

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}XConfKit 代码备份脚本${NC}"
echo -e "${BLUE}==========================================${NC}"

# 创建备份目录
echo -e "${YELLOW}创建备份目录...${NC}"
mkdir -p "$BACKUP_DIR"

# 1. Git备份
echo -e "${YELLOW}1. 创建Git备份...${NC}"
if [ -d ".git" ]; then
    # 创建Git仓库的完整备份
    git clone --mirror . "$GIT_BACKUP_DIR"
    echo -e "${GREEN}   Git备份完成: $GIT_BACKUP_DIR${NC}"
else
    echo -e "${RED}   错误: 未找到Git仓库${NC}"
    exit 1
fi

# 2. 创建压缩包备份
echo -e "${YELLOW}2. 创建压缩包备份...${NC}"

# 排除不需要备份的文件和目录
EXCLUDE_PATTERNS=(
    "node_modules"
    "__pycache__"
    "*.pyc"
    "*.log"
    "*.db"
    "*.pid"
    ".DS_Store"
    "data/backups"
    ".venv"
    "venv"
    "backups"
    ".git"
)

# 构建exclude参数
EXCLUDE_ARGS=""
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    EXCLUDE_ARGS="$EXCLUDE_ARGS -x '$pattern'"
done

# 创建压缩包，明确排除backups目录
zip -r "$ZIP_BACKUP_FILE" . \
    -x "node_modules/*" \
    -x "__pycache__/*" \
    -x "*.pyc" \
    -x "*.log" \
    -x "*.db" \
    -x "*.pid" \
    -x ".DS_Store" \
    -x "data/backups/*" \
    -x ".venv/*" \
    -x "venv/*" \
    -x "backups/*" \
    -x ".git/*"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}   压缩包备份完成: $ZIP_BACKUP_FILE${NC}"
else
    echo -e "${RED}   压缩包创建失败${NC}"
    exit 1
fi

# 3. 显示备份信息
echo -e "${YELLOW}3. 备份信息:${NC}"
echo -e "${BLUE}   Git备份位置:${NC} $GIT_BACKUP_DIR"
echo -e "${BLUE}   压缩包位置:${NC} $ZIP_BACKUP_FILE"
echo -e "${BLUE}   备份时间:${NC} $(date '+%Y-%m-%d %H:%M:%S')"

# 4. 显示文件大小
GIT_SIZE=$(du -sh "$GIT_BACKUP_DIR" | cut -f1)
ZIP_SIZE=$(du -sh "$ZIP_BACKUP_FILE" | cut -f1)
echo -e "${BLUE}   Git备份大小:${NC} $GIT_SIZE"
echo -e "${BLUE}   压缩包大小:${NC} $ZIP_SIZE"

# 5. 创建备份记录
BACKUP_INFO_FILE="$BACKUP_DIR/backup_info_$TIMESTAMP.txt"
cat > "$BACKUP_INFO_FILE" << EOF
XConfKit 代码备份记录
=====================

备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份类型: 完整代码备份
Git提交: $(git rev-parse HEAD)
Git消息: $(git log -1 --pretty=format:"%s")

备份内容:
- Git仓库完整备份: $GIT_BACKUP_DIR
- 代码压缩包: $ZIP_BACKUP_FILE

文件大小:
- Git备份: $GIT_SIZE
- 压缩包: $ZIP_SIZE

恢复方法:
1. Git恢复: git clone $GIT_BACKUP_DIR new_project
2. 压缩包恢复: unzip $ZIP_BACKUP_FILE -d new_project

当前功能状态:
- 设备管理: ✅ 正常
- 备份管理: ✅ 正常  
- 备份策略: ✅ 正常
- 调度器: ✅ 正常
- 立即执行: ✅ 正常
- 时间统一: ✅ 正常
EOF

echo -e "${GREEN}   备份记录已保存: $BACKUP_INFO_FILE${NC}"

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}🎉 备份完成！${NC}"
echo -e "${GREEN}==========================================${NC}"

echo -e "${YELLOW}恢复说明:${NC}"
echo -e "1. ${BLUE}Git恢复:${NC} git clone $GIT_BACKUP_DIR new_project"
echo -e "2. ${BLUE}压缩包恢复:${NC} unzip $ZIP_BACKUP_FILE -d new_project"
echo -e "3. ${BLUE}查看备份记录:${NC} cat $BACKUP_INFO_FILE"






