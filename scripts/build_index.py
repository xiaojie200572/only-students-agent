#!/usr/bin/env python3
"""
构建向量索引脚本

使用方法:
    python scripts/build_index.py              # 构建索引
    python scripts/build_index.py --rebuild   # 重建索引
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.vector.client import VectorStore
from app.config import get_settings

settings = get_settings()


async def main():
    parser = argparse.ArgumentParser(description="构建向量索引")
    parser.add_argument("--rebuild", action="store_true", help="重建索引")
    args = parser.parse_args()
    
    vector_store = VectorStore()
    
    if args.rebuild:
        print("重建索引...")
        vector_store.clear()
    else:
        count = vector_store.get_count()
        print(f"当前向量库中有 {count} 条笔记")
        print("索引已存在，如需重建请使用 --rebuild 参数")
        return
    
    print("索引构建完成!")


if __name__ == "__main__":
    asyncio.run(main())
