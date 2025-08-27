import requests
import json
import time

def test_google_flow_api():
    """Google Flow API'sini test et"""
    
    # Test data
    test_data = {
        "jobId": "test_job_8080",
        "prompt": "Bir köpek parkta koşuyor",
        "model": "google-flow",
        "timestamp": "2025-08-27T18:15:00Z",
        "userId": "test-user-8080",
        "action": "create_project",
        "timeout": 300,
        "callbackUrl": "https://balder-ai.vercel.app/api/jobs/callback"
    }
    
    # API endpoint
    url = "http://localhost:8080/api/v1/automation/google-flow"
    
    print("🧪 Google Flow API Test")
    print("=" * 40)
    print(f"URL: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print()
    
    try:
        # Send request
        print("📤 Request gönderiliyor...")
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 202:
            print("✅ API başarıyla çalışıyor!")
            return True
        else:
            print("❌ API hatası!")
            return False
            
    except Exception as e:
        print(f"❌ Request hatası: {e}")
        return False

def test_health_check():
    """Health check endpoint'ini test et"""
    
    url = "http://localhost:8080/health"
    
    print("🏥 Health Check Test")
    print("=" * 30)
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Health check başarılı!")
            return True
        else:
            print("❌ Health check başarısız!")
            return False
            
    except Exception as e:
        print(f"❌ Health check hatası: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Zendriver API Test Başlıyor...")
    print()
    
    # Health check
    health_ok = test_health_check()
    print()
    
    if health_ok:
        # Google Flow test
        test_google_flow_api()
    else:
        print("❌ API çalışmıyor, test durduruluyor.")
    
    print("\n🎉 Test tamamlandı!")
