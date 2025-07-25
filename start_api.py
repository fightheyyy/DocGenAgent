#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gauz文档Agent API 快速启动脚本
"""

import os
import sys

# 设置环境变量
os.environ['SKIP_HEALTH_CHECK'] = 'true'

if __name__ == "__main__":
    try:
        from api_server import start_server
        
        print("🚀 启动Gauz文档Agent API服务...")
        print("💡 提示：如需自定义配置，请直接运行 python api_server.py --help")
        
        # 使用默认配置启动
        start_server(host="0.0.0.0", port=8000, reload=False)
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请先安装依赖：pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1) 