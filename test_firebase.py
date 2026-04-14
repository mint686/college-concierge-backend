from notification_service import firebase_ready, init_firebase

print(f"Firebase ready: {firebase_ready}")

if not firebase_ready:
    print("Trying to initialize again...")
    init_firebase()