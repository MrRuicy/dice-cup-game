#!/bin/bash
set -e

echo "🚀 准备部署到魔搭社区创空间..."

# 1. 检查前端目录
if [ ! -d "frontend" ]; then
    echo "❌ 错误: frontend 目录不存在"
    exit 1
fi

# 2. 构建前端
echo "📦 构建前端..."
cd frontend
npm install
npm run build

# 3. 复制静态文件到后端
echo "📋 复制静态文件..."
cd ..
rm -rf backend/static
cp -r frontend/dist backend/static

# 4. 创建部署包
echo "📦 创建部署包..."
rm -rf deploy_package
mkdir -p deploy_package

# 复制后端文件
cp backend/*.py deploy_package/
cp backend/requirements_gradio.txt deploy_package/requirements.txt
cp -r backend/static deploy_package/static

# 复制 README
cp README_MODELSCOPE.md deploy_package/README.md

# 5. 生成打包文件
echo "🗜️  打包..."
cd deploy_package
zip -r ../dice-game-modelscope.zip .
cd ..

echo ""
echo "✅ 部署包已准备完成！"
echo ""
echo "📦 部署包位置:"
echo "   - 目录: deploy_package/"
echo "   - 压缩包: dice-game-modelscope.zip"
echo ""
echo "📋 部署步骤:"
echo "   1. 访问 https://www.modelscope.cn/my/myspaces"
echo "   2. 点击「创建空间」"
echo "   3. 选择 SDK: Gradio"
echo "   4. 上传 dice-game-modelscope.zip 或 deploy_package/ 目录"
echo "   5. 等待构建完成"
echo ""
echo "🎮 开始游戏！"
