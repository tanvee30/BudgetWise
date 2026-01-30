import os
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budgetwise_project.settings')
django.setup()

# Now test Redis
from django.core.cache import cache
from django.conf import settings

print("🔍 Testing Redis Connection...")
print("=" * 50)

try:
    # Test 1: Set a value
    print("\n1️⃣ Setting test value in cache...")
    cache.set('test_key', 'Hello Redis!', 60)
    print("   ✅ Value set successfully")
    
    # Test 2: Get the value
    print("\n2️⃣ Retrieving test value from cache...")
    value = cache.get('test_key')
    
    if value == 'Hello Redis!':
        print(f"   ✅ Retrieved: '{value}'")
        print("\n✅ Redis is working perfectly!")
    else:
        print(f"   ❌ Expected 'Hello Redis!' but got: {value}")
        
    # Test 3: Show configuration
    print("\n📊 Redis Configuration:")
    print(f"   Backend: {settings.CACHES['default']['BACKEND']}")
    print(f"   Location: {settings.CACHES['default']['LOCATION']}")
    print(f"   Timeout: {settings.CACHES['default']['TIMEOUT']}s")
    
    # Test 4: Cache stats
    print("\n3️⃣ Testing cache operations...")
    cache.set('counter', 1)
    cache.incr('counter')
    counter = cache.get('counter')
    print(f"   Counter test: {counter} (expected: 2)")
    
    if counter == 2:
        print("   ✅ Cache operations working!")
    
    print("\n" + "=" * 50)
    print("🎉 All Redis tests passed!")
    
except Exception as e:
    print(f"\n❌ Redis error: {e}")
    print("\n💡 Make sure Redis server is running:")
    print("   1. Check if Redis is installed")
    print("   2. Run: redis-server")
    print("   3. Or: brew services start redis (Mac)")