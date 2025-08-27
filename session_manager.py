import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SessionManager:
    """Session ve credentials yönetimi - Normal account girişi"""
    
    def __init__(self):
        self.credentials_file = "credentials.json"
        self.session_file = "session.json"
        
    def save_credentials(self, email: str, password: str, is_first_login: bool = True):
        """Credentials'ları kaydet - Açık metin"""
        try:
            credentials = {
                "email": email,
                "password": password,
                "is_first_login": is_first_login,
                "created_at": datetime.now().isoformat()
            }
            
            # Açık metin olarak kaydet
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=2, ensure_ascii=False)
            
            logger.info("Credentials başarıyla kaydedildi")
            return True
            
        except Exception as e:
            logger.error(f"Credentials kaydetme hatası: {e}")
            return False
    
    def get_current_credentials(self):
        """Mevcut credentials'ları al - Açık metin"""
        try:
            if not os.path.exists(self.credentials_file):
                logger.warning("Credentials dosyası bulunamadı")
                return None
            
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(self.credentials_file, 'r', encoding=encoding) as f:
                        credentials = json.load(f)
                    
                    logger.info(f"Credentials başarıyla alındı (encoding: {encoding})")
                    return credentials
                    
                except UnicodeDecodeError:
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error with {encoding}: {e}")
                    continue
            
            logger.error("Credentials dosyası hiçbir encoding ile okunamadı")
            return None
            
        except Exception as e:
            logger.error(f"Credentials alma hatası: {e}")
            return None
    
    def update_credentials(self, email: str = None, password: str = None):
        """Credentials'ları güncelle"""
        try:
            current = self.get_current_credentials()
            if not current:
                return self.save_credentials(email, password)
            
            if email:
                current["email"] = email
            if password:
                current["password"] = password
            
            current["updated_at"] = datetime.now().isoformat()
            
            # Açık metin olarak kaydet
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
            
            logger.info("Credentials başarıyla güncellendi")
            return True
            
        except Exception as e:
            logger.error(f"Credentials güncelleme hatası: {e}")
            return False
    
    def delete_credentials(self):
        """Credentials'ları sil"""
        try:
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
                logger.info("Credentials başarıyla silindi")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Credentials silme hatası: {e}")
            return False
    
    def save_session(self, session_data: dict):
        """Session verilerini kaydet"""
        try:
            session_data["created_at"] = datetime.now().isoformat()
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            logger.info("Session verileri kaydedildi")
            return True
            
        except Exception as e:
            logger.error(f"Session kaydetme hatası: {e}")
            return False
    
    def get_session(self):
        """Session verilerini al"""
        try:
            if not os.path.exists(self.session_file):
                return None
            
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            return session_data
            
        except Exception as e:
            logger.error(f"Session alma hatası: {e}")
            return None
    
    def clear_session(self):
        """Session verilerini temizle"""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                logger.info("Session verileri temizlendi")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Session temizleme hatası: {e}")
            return False
    
    def is_session_valid(self, max_age_hours: int = 24):
        """Session'ın geçerli olup olmadığını kontrol et"""
        try:
            session = self.get_session()
            if not session:
                return False
            
            created_at = datetime.fromisoformat(session["created_at"])
            max_age = timedelta(hours=max_age_hours)
            
            return datetime.now() - created_at < max_age
            
        except Exception as e:
            logger.error(f"Session geçerlilik kontrolü hatası: {e}")
            return False
    
    def is_first_login(self):
        """İlk giriş olup olmadığını kontrol et"""
        try:
            credentials = self.get_current_credentials()
            if not credentials:
                return True  # Credentials yoksa ilk giriş kabul et
            
            return credentials.get("is_first_login", True)
            
        except Exception as e:
            logger.error(f"İlk giriş kontrolü hatası: {e}")
            return True
    
    def mark_onboarding_completed(self):
        """Onboarding'in tamamlandığını işaretle"""
        try:
            credentials = self.get_current_credentials()
            if not credentials:
                logger.warning("Mark edilecek credentials bulunamadı")
                return False
            
            credentials["is_first_login"] = False
            credentials["onboarding_completed_at"] = datetime.now().isoformat()
            
            # Açık metin olarak kaydet
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(credentials, f, indent=2, ensure_ascii=False)
            
            logger.info("Onboarding tamamlandı olarak işaretlendi")
            return True
            
        except Exception as e:
            logger.error(f"Onboarding işaretleme hatası: {e}")
            return False

# Test fonksiyonu
def test_session_manager():
    """Session manager'ı test et"""
    print("🧪 Session Manager Test - Normal Account Girişi")
    print("=" * 50)
    
    sm = SessionManager()
    
    # Test credentials
    print("1. Credentials kaydetme testi...")
    success = sm.save_credentials("test@example.com", "testpassword123")
    print(f"   Sonuç: {'✅ Başarılı' if success else '❌ Başarısız'}")
    
    print("\n2. Credentials alma testi...")
    creds = sm.get_current_credentials()
    if creds:
        print(f"   Email: {creds['email']}")
        print(f"   Password: {creds['password']}")  # Açık metin göster
        print("   ✅ Başarılı")
    else:
        print("   ❌ Başarısız")
    
    print("\n3. Session kaydetme testi...")
    session_data = {
        "user_id": "test_user_123",
        "status": "logged_in",
        "last_activity": datetime.now().isoformat()
    }
    success = sm.save_session(session_data)
    print(f"   Sonuç: {'✅ Başarılı' if success else '❌ Başarısız'}")
    
    print("\n4. Session alma testi...")
    session = sm.get_session()
    if session:
        print(f"   User ID: {session['user_id']}")
        print(f"   Status: {session['status']}")
        print("   ✅ Başarılı")
    else:
        print("   ❌ Başarısız")
    
    print("\n5. Session geçerlilik testi...")
    is_valid = sm.is_session_valid()
    print(f"   Sonuç: {'✅ Geçerli' if is_valid else '❌ Geçersiz'}")
    
    print("\n🎉 Test tamamlandı!")

if __name__ == "__main__":
    test_session_manager()
