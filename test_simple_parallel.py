#!/usr/bin/env python3

import asyncio
import time
import openai
from concurrent.futures import ThreadPoolExecutor

async def simple_parallel_test():
    """Test if we can make parallel LLM calls"""
    
    # Create client
    client = openai.OpenAI(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio"
    )
    
    # Get model
    model = client.models.list().data[0].id
    
    cities = ["Tokyo", "London", "New York", "Sydney"]
    
    print("🚀 Testing simple parallel LLM calls...")
    start_time = time.time()
    
    async def make_llm_call(city):
        call_start = time.time()
        print(f"📡 Starting LLM call for {city}...")
        
        # Run the synchronous LLM call in a thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a weather assistant. Be brief."},
                    {"role": "user", "content": f"What's the weather like in {city}? Just make something up."}
                ],
                temperature=0.3
            )
        )
        
        call_time = time.time() - call_start
        result = response.choices[0].message.content
        print(f"✅ {city} completed in {call_time:.2f}s: {result[:30]}...")
        return result
    
    # Make all calls in parallel
    tasks = [make_llm_call(city) for city in cities]
    results = await asyncio.gather(*tasks)
    
    parallel_time = time.time() - start_time
    print(f"\n✅ All parallel calls completed in {parallel_time:.2f} seconds")
    
    # Now test sequential calls
    print("\n🐌 Testing sequential LLM calls...")
    start_time = time.time()
    
    sequential_results = []
    for city in cities:
        call_start = time.time()
        print(f"📡 Starting sequential LLM call for {city}...")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a weather assistant. Be brief."},
                {"role": "user", "content": f"What's the weather like in {city}? Just make something up."}
            ],
            temperature=0.3
        )
        
        call_time = time.time() - call_start
        result = response.choices[0].message.content
        print(f"✅ {city} completed in {call_time:.2f}s: {result[:30]}...")
        sequential_results.append(result)
    
    sequential_time = time.time() - start_time
    print(f"\n✅ All sequential calls completed in {sequential_time:.2f} seconds")
    
    print(f"\n📊 Performance comparison:")
    print(f"  Parallel:   {parallel_time:.2f} seconds")
    print(f"  Sequential: {sequential_time:.2f} seconds")
    if sequential_time > parallel_time:
        print(f"  Speedup:    {sequential_time/parallel_time:.2f}x faster with parallel execution")
    else:
        print(f"  No speedup - parallel was {parallel_time/sequential_time:.2f}x slower")

if __name__ == "__main__":
    asyncio.run(simple_parallel_test())
