#!/usr/bin/env python3
"""
笔记同步脚本 - 从Java后端获取笔记并同步到向量库

使用方法:
    python scripts/sync_notes.py              # 增量同步
    python scripts/sync_notes.py --full       # 全量同步
    python scripts/sync_notes.py --since 123  # 从指定ID开始同步
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.vector.ingest import NoteIngestor


async def main():
    parser = argparse.ArgumentParser(description="同步笔记到向量库")
    parser.add_argument("--full", action="store_true", help="全量同步（先清空再导入）")
    parser.add_argument("--since", type=int, help="从指定笔记ID开始同步")
    args = parser.parse_args()
    
    ingestor = NoteIngestor()
    
    status = ingestor.get_sync_status()
    print(f"当前状态: {status}")
    
    print(f"开始同步...")
    count = await ingestor.sync_notes(
        full_sync=args.full,
        since_id=args.since,
    )
    
    print(f"\n同步完成! 共同步 {count} 条笔记")
    
    final_status = ingestor.get_sync_status()
    print(f"最终状态: {final_status}")


if __name__ == "__main__":
    asyncio.run(main())
