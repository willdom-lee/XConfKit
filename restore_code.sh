#!/bin/bash

# XConfKit 代码恢复脚本
# 用于从备份中恢复代码

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKUP_DIR="./backups"

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}XConfKit 代码恢复脚本${NC}"
echo -e "${BLUE}==========================================${NC}"

# 检查备份目录是否存在
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}错误: 备份目录不存在 ($BACKUP_DIR)${NC}"
    exit 1
fi

# 查找最新的备份
echo -e "${YELLOW}查找可用备份...${NC}"

# 查找最新的Git备份
LATEST_GIT_BACKUP=$(ls -td "$BACKUP_DIR"/git_backup_* 2>/dev/null | head -1)
if [ -z "$LATEST_GIT_BACKUP" ]; then
    echo -e "${RED}错误: 未找到Git备份${NC}"
    exit 1
fi

# 查找最新的压缩包备份
LATEST_ZIP_BACKUP=$(ls -t "$BACKUP_DIR"/XConfKit202508_backup_*.zip 2>/dev/null | head -1)
if [ -z "$LATEST_ZIP_BACKUP" ]; then
    echo -e "${RED}错误: 未找到压缩包备份${NC}"
    exit 1
fi

# 查找最新的备份信息文件
LATEST_INFO_FILE=$(ls -t "$BACKUP_DIR"/backup_info_*.txt 2>/dev/null | head -1)

echo -e "${GREEN}找到备份:${NC}"
echo -e "  Git备份: ${BLUE}$(basename "$LATEST_GIT_BACKUP")${NC}"
echo -e "  压缩包: ${BLUE}$(basename "$LATEST_ZIP_BACKUP")${NC}"
if [ -n "$LATEST_INFO_FILE" ]; then
    echo -e "  信息文件: ${BLUE}$(basename "$LATEST_INFO_FILE")${NC}"
fi

# 显示备份信息
if [ -n "$LATEST_INFO_FILE" ]; then
    echo -e "\n${YELLOW}备份信息:${NC}"
    cat "$LATEST_INFO_FILE"
fi

echo -e "\n${YELLOW}选择恢复方式:${NC}"
echo -e "1. ${BLUE}Git恢复${NC} - 恢复完整的Git历史（推荐）"
echo -e "2. ${BLUE}压缩包恢复${NC} - 恢复代码文件（不含Git历史）"
echo -e "3. ${BLUE}查看备份详情${NC} - 显示备份内容"

read -p "请选择 (1-3): " choice

case $choice in
    1)
        echo -e "\n${YELLOW}执行Git恢复...${NC}"
        read -p "请输入恢复目录名称 (默认: XConfKit_restored): " restore_dir
        restore_dir=${restore_dir:-XConfKit_restored}
        
        if [ -d "$restore_dir" ]; then
            echo -e "${RED}错误: 目录 $restore_dir 已存在${NC}"
            exit 1
        fi
        
        echo -e "${YELLOW}正在恢复Git仓库...${NC}"
        git clone "$LATEST_GIT_BACKUP" "$restore_dir"
        
        echo -e "${GREEN}Git恢复完成！${NC}"
        echo -e "恢复位置: ${BLUE}$restore_dir${NC}"
        echo -e "进入目录: ${BLUE}cd $restore_dir${NC}"
        echo -e "启动服务: ${BLUE}./start_services.sh${NC}"
        ;;
        
    2)
        echo -e "\n${YELLOW}执行压缩包恢复...${NC}"
        read -p "请输入恢复目录名称 (默认: XConfKit_restored): " restore_dir
        restore_dir=${restore_dir:-XConfKit_restored}
        
        if [ -d "$restore_dir" ]; then
            echo -e "${RED}错误: 目录 $restore_dir 已存在${NC}"
            exit 1
        fi
        
        echo -e "${YELLOW}正在解压备份文件...${NC}"
        unzip "$LATEST_ZIP_BACKUP" -d "$restore_dir"
        
        echo -e "${GREEN}压缩包恢复完成！${NC}"
        echo -e "恢复位置: ${BLUE}$restore_dir${NC}"
        echo -e "进入目录: ${BLUE}cd $restore_dir${NC}"
        echo -e "启动服务: ${BLUE}./start_services.sh${NC}"
        ;;
        
    3)
        echo -e "\n${YELLOW}备份详情:${NC}"
        if [ -n "$LATEST_INFO_FILE" ]; then
            cat "$LATEST_INFO_FILE"
        else
            echo -e "${BLUE}Git备份:${NC} $LATEST_GIT_BACKUP"
            echo -e "${BLUE}压缩包:${NC} $LATEST_ZIP_BACKUP"
            echo -e "${BLUE}备份时间:${NC} $(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$LATEST_ZIP_BACKUP")"
        fi
        ;;
        
    *)
        echo -e "${RED}无效选择${NC}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}==========================================${NC}"
echo -e "${GREEN}恢复操作完成！${NC}"
echo -e "${GREEN}==========================================${NC}"






