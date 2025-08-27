# Zendriver Integration Specification

## Mevcut Jobs API Yapısı (Appium)

### Endpoint
```
https://immensely-ace-jaguar.ngrok-free.app/api/v1/automation/google-flow
```

### Request Format
**Method**: POST

**Headers**:
```json
{
  "Content-Type": "application/json",
  "Origin": "https://balder-ai.vercel.app",
  "Connection": "keep-alive",
  "Cache-Control": "no-cache",
  "User-Agent": "BalderAI/1.0"
}
```

**Request Body**:
```json
{
  "jobId": "unique_website_job_id_1755925204612_4uvbgrvys",
  "prompt": "user prompt",
  "model": "model name",
  "timestamp": "2024-01-20T10:30:00.000Z",
  "userId": "user-id",
  "action": "create_project",
  "timeout": 300,
  "callbackUrl": "https://balder-ai.vercel.app/api/jobs/callback"
}
```

## Zendriver Entegrasyonu - Aynı Yapıyı Kullan

### 1. Mevcut Endpoint'e Zendriver Desteği Ekle
Aynı endpoint'i kullan, sadece action'a göre Zendriver veya Appium seç:

```python
# Aynı endpoint, farklı action handling
@app.route('/api/v1/automation/google-flow', methods=['POST'])
def automation_handler():
    data = request.json
    
    # Gelen verileri al
    job_id = data.get('jobId')
    prompt = data.get('prompt')
    model = data.get('model')
    timestamp = data.get('timestamp')
    user_id = data.get('userId')
    action = data.get('action')
    timeout = data.get('timeout')
    callback_url = data.get('callbackUrl')
    
         # Şu anlık sadece Zendriver kullan (test için)
     if action == "create_project":
         return process_zendriver_job(data)  # Zendriver logic
```

### 2. Request Body Validation
```python
def validate_request(data):
    required_fields = ['jobId', 'prompt', 'model', 'timestamp', 'userId', 'action', 'timeout', 'callbackUrl']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    return True, "Valid request"
```

### 3. Callback URL Implementation
```python
import requests

def send_callback(callback_url, job_id, status, result_url=None, error=None):
    callback_data = {
        "jobId": job_id,
        "status": status,  # "completed", "failed", "processing"
        "resultUrl": result_url,
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        response = requests.post(callback_url, json=callback_data, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"Callback failed: {e}")
        return False
```

### 4. Retry Mechanism
```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator
```

### 5. Zendriver Session Management (Appium Pattern'ine Uygun)
```python
class ZendriverSession:
    def __init__(self, job_id, user_id):
        self.job_id = job_id
        self.user_id = user_id
        self.session_id = None
        self.status = "initializing"
        
    def create_session(self):
        # Appium'daki gibi session oluştur
        # Aynı response format'ını kullan
        pass
        
    def navigate_to_url(self, url):
        # Appium'daki gibi navigate
        pass
        
    def find_element(self, selector, selector_type="css"):
        # Appium'daki gibi element bul
        pass
        
    def click_element(self, element_id):
        # Appium'daki gibi click
        pass
        
    def send_keys(self, element_id, text):
        # Appium'daki gibi send keys
        pass
        
    def take_screenshot(self):
        # Appium'daki gibi screenshot al
        pass
        
    def close_session(self):
        # Appium'daki gibi session kapat
        pass
```

### 6. Main Processing Function
```python
@retry_on_failure(max_retries=3)
def process_zendriver_job(job_data):
    job_id = job_data['jobId']
    user_id = job_data['userId']
    prompt = job_data['prompt']
    callback_url = job_data['callbackUrl']
    
    # Callback: Processing başladı
    send_callback(callback_url, job_id, "processing")
    
    try:
        # Zendriver session oluştur
        session = ZendriverSession(job_id, user_id)
        session.create_session()
        
        # Prompt'u parse et ve işlemleri yap
        # ...
        
        # Screenshot al ve kaydet
        screenshot_path = session.take_screenshot()
        
        # Callback: Başarılı
        send_callback(callback_url, job_id, "completed", result_url=screenshot_path)
        
    except Exception as e:
        # Callback: Hata
        send_callback(callback_url, job_id, "failed", error=str(e))
        raise e
```

### 7. Error Handling
```python
def handle_zendriver_error(error, job_id, callback_url):
    error_messages = {
        "session_creation_failed": "Zendriver session oluşturulamadı",
        "element_not_found": "Element bulunamadı",
        "timeout": "İşlem zaman aşımına uğradı",
        "navigation_failed": "Sayfa yüklenemedi"
    }
    
    error_msg = error_messages.get(str(error), str(error))
    send_callback(callback_url, job_id, "failed", error=error_msg)
```

### 8. Environment Variables
```python
import os

ZENDRIVER_URL = os.getenv('ZENDRIVER_URL', 'http://localhost:4444')
CALLBACK_TIMEOUT = int(os.getenv('CALLBACK_TIMEOUT', '30'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
JOB_TIMEOUT = int(os.getenv('JOB_TIMEOUT', '300'))
```

### 9. Logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_job_event(job_id, event, details=None):
    logger.info(f"Job {job_id}: {event} - {details}")
```

### 10. Health Check Endpoint
```python
@app.route('/health', methods=['GET'])
def health_check():
    return {
        "status": "healthy",
        "service": "zendriver-automation",
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Entegrasyon Adımları

1. **Appium'ı Zendriver ile değiştir** (test için)
2. **Appium pattern'ini kopyala** (aynı request/response format)
3. **Aynı callback URL mechanism'ini kullan**
4. **Aynı retry logic'i kullan**
5. **Aynı error handling'i kullan**
6. **Aynı logging pattern'ini kullan**
7. **Aynı health check endpoint'ini kullan**
8. **Aynı environment variables yapısını kullan**

## Test Senaryoları

1. **Başarılı job processing**
2. **Element bulunamadı hatası**
3. **Session creation hatası**
4. **Timeout durumu**
5. **Callback URL hatası**
6. **Retry mechanism testi**

## Önemli Notlar

- **Aynı endpoint kullan**: `/api/v1/automation/google-flow`
- **Aynı request format**: Appium ile tamamen aynı
- **Aynı response format**: Appium ile tamamen aynı
- **Aynı callback URL**: `https://balder-ai.vercel.app/api/jobs/callback`
- **Aynı headers**: Content-Type, Origin, Connection, Cache-Control, User-Agent
- **Aynı timeout**: 120 saniye
- **Aynı retry mechanism**: 5 deneme, exponential backoff

Şu anlık test için Appium'ın yerine Zendriver kullanılacak. Tüm request'ler Zendriver'a yönlendirilecek. Hiçbir ayırt etme logic'i olmayacak.

Bu specification ile diğer agent, Appium'ın tam olarak aynı pattern'ini kullanarak Zendriver entegrasyonunu implement edebilir.
