import firebase_admin
from firebase_admin import credentials, messaging
import os
import json

# Path to your service account key
cred_path = "firebase-service-account.json"

# Initialize Firebase
def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        if not firebase_admin._apps:
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase initialized successfully!")
                return True
            else:
                print(f"❌ Firebase credentials not found at: {os.path.abspath(cred_path)}")
                return False
        else:
            print("✅ Firebase already initialized")
            return True
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        return False

# Initialize on import
firebase_ready = init_firebase()

def send_push_notification(device_token: str, title: str, body: str, data: dict = None):
    """Send push notification to a specific device"""
    
    if not firebase_ready:
        print("❌ Firebase not initialized")
        return None
    
    if not device_token:
        print("❌ No device token provided")
        return None
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            token=device_token
        )
        
        response = messaging.send(message)
        print(f"✅ Notification sent! Response: {response}")
        return response
        
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")
        return None