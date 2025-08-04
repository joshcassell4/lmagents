#!/usr/bin/env python3

import asyncio
from agent import demo_parallel_agents

if __name__ == "__main__":
    print("🚀 Testing Parallel vs Sequential Agent Execution")
    print("=" * 60)
    asyncio.run(demo_parallel_agents())
