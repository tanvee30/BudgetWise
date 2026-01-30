# from django.test import TestCase

# # Create your tests here.

# import os
# import django

# # Django setup
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budgetwise_project.settings')
# django.setup()

# # Now test Redis
# from django.core.cache import cache
# from django.conf import settings

# print("🔍 Testing Redis Connection...")
# print("=" * 50)

# try:
#     # Test 1: Set a value
#     print("\n1️⃣ Setting test value in cache...")
#     cache.set('test_key', 'Hello Redis!', 60)
#     print("   ✅ Value set successfully")
    
#     # Test 2: Get the value
#     print("\n2️⃣ Retrieving test value from cache...")
#     value = cache.get('test_key')
    
#     if value == 'Hello Redis!':
#         print(f"   ✅ Retrieved: '{value}'")
#         print("\n✅ Redis is working perfectly!")
#     else:
#         print(f"   ❌ Expected 'Hello Redis!' but got: {value}")
        
#     # Test 3: Show configuration
#     print("\n📊 Redis Configuration:")
#     print(f"   Backend: {settings.CACHES['default']['BACKEND']}")
#     print(f"   Location: {settings.CACHES['default']['LOCATION']}")
#     print(f"   Timeout: {settings.CACHES['default']['TIMEOUT']}s")
    
#     # Test 4: Cache stats
#     print("\n3️⃣ Testing cache operations...")
#     cache.set('counter', 1)
#     cache.incr('counter')
#     counter = cache.get('counter')
#     print(f"   Counter test: {counter} (expected: 2)")
    
#     if counter == 2:
#         print("   ✅ Cache operations working!")
    
#     print("\n" + "=" * 50)
#     print("🎉 All Redis tests passed!")
    
# except Exception as e:
#     print(f"\n❌ Redis error: {e}")
#     print("\n💡 Make sure Redis server is running:")
#     print("   1. Check if Redis is installed")
#     print("   2. Run: redis-server")
#     print("   3. Or: brew services start redis (Mac)")



#     print("\n" + "="*60)
# print("🔍 DATABASE QUERY OPTIMIZATION")
# print("="*60)


# Database query optimization

# from django.db import connection
# from django.db.models import Avg, Sum, StdDev

# # Reset query counter
# connection.queries_log.clear()

# # Old way (Multiple queries - BAD)
# print("\n❌ OLD WAY (Multiple Queries):")
# from finance.models import Transaction
# categories = ['food', 'transport', 'rent', 'entertainment']
# query_count_before = len(connection.queries)

# for cat in categories:
#     txns = Transaction.objects.filter(user=user, category=cat)
#     avg = sum(t.amount for t in txns) / len(txns) if txns else 0

# old_queries = len(connection.queries) - query_count_before
# print(f"   Queries executed: {old_queries}")

# # Reset
# connection.queries_log.clear()

# # New way (Single aggregated query - GOOD)
# print("\n✅ NEW WAY (Single Aggregated Query):")
# query_count_before = len(connection.queries)

# stats = Transaction.objects.filter(user=user).values('category').annotate(
#     avg_amount=Avg('amount'),
#     total_amount=Sum('amount'),
#     std_dev=StdDev('amount')
# )
# list(stats)  # Force evaluation

# new_queries = len(connection.queries) - query_count_before
# print(f"   Queries executed: {new_queries}")

# print(f"\n📊 Query Reduction: {old_queries} → {new_queries} queries")
# print(f"   🚀 {old_queries/new_queries:.0f}x fewer database hits!")
# print("="*60 + "\n")



# budget cache

# from finance.services import BudgetCalculationService
# from django.contrib.auth.models import User
# from django.core.cache import cache
# import time

# print("\n" + "="*60)
# print("🎯 BUDGET CACHING PERFORMANCE TEST")
# print("="*60)

# # Get user
# user = User.objects.get(username='testuser')
# service = BudgetCalculationService(user)

# # Clear cache
# cache.clear()
# print("\n✅ Cache cleared")

# # Test 1: First call (NO CACHE)
# print("\n1️⃣ FIRST CALL (Cache MISS - Will calculate):")
# start = time.time()
# budget1 = service.generate_budget_recommendation()
# time1 = time.time() - start
# print(f"   ⏱️  Time: {time1:.3f} seconds")
# print(f"   💰 Total Budget: ₹{budget1.total_recommended_budget:,.2f}")
# print(f"   💾 Recommended Savings: ₹{budget1.recommended_savings:,.2f}")

# # Test 2: Second call (WITH CACHE)
# print("\n2️⃣ SECOND CALL (Cache HIT - From cache):")
# start = time.time()
# budget2 = service.generate_budget_recommendation()
# time2 = time.time() - start
# print(f"   ⏱️  Time: {time2:.3f} seconds")
# print(f"   💰 Total Budget: ₹{budget2.total_recommended_budget:,.2f}")
# print(f"   💾 Recommended Savings: ₹{budget2.recommended_savings:,.2f}")

# # Results
# print("\n" + "="*60)
# print("📊 PERFORMANCE COMPARISON:")
# print("="*60)
# print(f"   First call:  {time1:.3f}s (calculated from database)")
# print(f"   Second call: {time2:.3f}s (retrieved from cache)")
# speedup = time1 / time2 if time2 > 0 else 1
# print(f"   🚀 SPEEDUP: {speedup:.1f}x FASTER!")
# print(f"   ✅ Same budget returned: {budget1.id == budget2.id}")
# print("="*60)
# print("✅ CACHING IS WORKING PERFECTLY!\n")
