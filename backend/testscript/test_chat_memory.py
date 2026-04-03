import requests
import json
import time
import websocket
import uuid
import threading
import os
import jwt
from datetime import datetime, timezone
from chat_messages import python_messages, javascript_messages, digital_marketing_messages, seo_messages

API_URL = "http://localhost:8000/api/v1"
AUTH_ENDPOINT = f"{API_URL}/auth/register-or-login"
USER_DELETE_ENDPOINT = f"{API_URL}/users"
CHAT_ENDPOINT = "ws://localhost:8000/api/v1/chat/ws"
ADMIN_KEY = "dev-admin-key"
ADMIN_DELETE_ENDPOINT = f"{API_URL}/admin/delete-user"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(BASE_DIR, "chat_logs.txt")


users = [
    {"email": f"poonderr_users{i}@gmail.com", "password": "Test@1234", "username": f"pon_user{i}"}
    for i in range(1, 11)
]


topics_messages = {
    "Python": python_messages,
    "Digital Marketing": digital_marketing_messages,
    "SEO": seo_messages,
    "JavaScript": javascript_messages
}


def log_to_file(text: str):
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(text + "\n")



def create_dummy_admin():
    payload = {
        "email": "admiiin_ponder@gmail.com",
        "password": "Admin@123",
        "is_new_user": False,
        "username": "admin_test"
    }

    try:
        res = requests.post(AUTH_ENDPOINT, headers=HEADERS, data=json.dumps(payload))
        if res.status_code == 200:
            print("Dummy admin login OK.")
            token = res.json().get("access_token")
            # promote_admin(token)  
            return token
        else:
            print(f"Admin login failed: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Admin login exception: {e}")
    return None


# def promote_admin(token: str):
#     promote_response = requests.patch(
#         url=f"{API_URL}/api/v1/users/promote",
#         headers={"Authorization": f"Bearer {token}"}, 
#         json={"email": "user_to_promote@gmail.com"}
#     )
#     print("$$$$$$$$$$$$",promote_response)
#     if promote_response.status_code == 200:
#         print("[✓] Admin promoted via API.")
#     else:
#         print(f"[!] Failed to promote admin: {promote_response.status_code} - {promote_response.text}")


 



admin_token = create_dummy_admin()
if not admin_token:
    print("Admin token not available. Exiting.")
    exit(1)

# Safe to decode now
decoded = jwt.decode(admin_token.encode(), options={"verify_signature": False})
print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", decoded)




def register_or_login_user(user):
    payload = {
        "email": user["email"],
        "password": user["password"],
        "is_new_user": True,
        "username": user["username"]
    }

    try:
        res = requests.post(AUTH_ENDPOINT, headers=HEADERS, data=json.dumps(payload))
        if res.status_code == 200:
            print(f"Auth OK: {user['email']}")
            return res.json().get("access_token")
        else:
            print(f"Auth Failed: {user['email']} -> {res.status_code} {res.text}")
            return None
    except Exception as e:
        print(f"[!] Exception on auth: {user['email']} -> {e}")
        return None


admin_token = None  

def delete_user_as_admin(user_id, topic):
    try:
        headers = {
            "Authorization": f"Bearer {admin_token}" if admin_token else "",
            "Content-Type": "application/json"
        }
        print("####################",user_id,topic)
        res = requests.delete(f"{ADMIN_DELETE_ENDPOINT}/{user_id}", headers=headers)
        print("(((((((((((((((((((((((((((((((((((((((())))))))))))))))))))))))))))))))))))))))",res)
        if res.status_code == 200:
            print(f"[{topic}] Admin deleted user: {user_id}")
            log_to_file(f"[{topic}] Admin deleted user: {user_id}")
        else:
            print(f"[{topic}] Admin delete failed: {res.status_code} - {res.text}")
            log_to_file(f"[{topic}] Admin delete failed: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[{topic}] Exception in admin delete: {e}")
        log_to_file(f"[{topic}] Exception in admin delete: {e}")


def chat_session(token, messages, topic):
    session_id = str(uuid.uuid4())
    chat_history = []
    message_index = 0
    message_time_map = {}

    def on_message(ws, response):
        nonlocal message_index
        data = json.loads(response)

        if data.get("type") == "system" and data.get("status") == "acknowledged":
            return

        if data.get("sender") == "bot" and "text" in data:
            receive_time = datetime.now(timezone.utc)
            last_user_msg = chat_history[-1]["content"] if chat_history and chat_history[-1]["role"] == "user" else None
            sent_time = message_time_map.get(last_user_msg)
            response_time = (receive_time - sent_time).total_seconds() if sent_time else None

            log_entry = (
                f"[{topic}] Assistant Response to: '{last_user_msg}'\n"
                f"→ {data['text']}\n"
                f"Response Time: {response_time:.2f} sec\n"
                f"---------------------------"
            )
            print(log_entry)
            log_to_file(log_entry)

            chat_history.append({"role": "assistant", "content": data["text"]})

            if message_index < len(messages):
                user_message = messages[message_index]
                chat_history.append({"role": "user", "content": user_message})
                msg_payload = {
                    "type": "message",
                    "session_id": session_id,
                    "message": user_message,
                    "chat_history": chat_history,
                    "agent_mode": "learning",
                    "chat_mode": "memory"
                }
                message_time_map[user_message] = datetime.now(timezone.utc)
                ws.send(json.dumps(msg_payload))
                print(f"[{topic}] Sent: {user_message}")
                message_index += 1
            else:
                print(f"[{topic}]  All messages sent.")
                ws.close()
        else:
            print(f"[{topic}]  Unrecognized response: {data}")
            log_to_file(f"[{topic}]  Unrecognized response: {data}")

    def on_open(ws):
        print(f"[{topic}]  Connection Opened")
        auth_payload = {
            "type": "auth",
            "session_id": session_id,
            "token": token
        }
        ws.send(json.dumps(auth_payload))
        time.sleep(1)

        if messages:
            first_msg = messages[0]
            chat_history.append({"role": "user", "content": first_msg})
            message_time_map[first_msg] = datetime.now(timezone.utc)
            ws.send(json.dumps({
                "type": "message",
                "session_id": session_id,
                "message": first_msg,
                "chat_history": chat_history,
                "agent_mode": "learning",
                "chat_mode": "memory"
            }))
            print(f"[{topic}] Sent: {first_msg}")
            nonlocal message_index
            message_index = 1

    def on_error(ws, error):
        print(f"[{topic}]  WebSocket Error: {error}")
        log_to_file(f"[{topic}]  WebSocket Error: {error}")

    def on_close(ws, *args):
        print(f"[{topic}]  Connection Closed")
        log_to_file(f"[{topic}]  Connection Closed")

        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            user_id = decoded.get("sub") or decoded.get("user_id")
            if user_id:
                 delete_user_as_admin(user_id, topic)
        except Exception as e:
            print(f"[{topic}]  Failed to decode JWT for delete: {e}")


    ws = websocket.WebSocketApp(
        CHAT_ENDPOINT,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()




# Start chat sessions
admin_token = create_dummy_admin()
if not admin_token:
    print("Cannot continue without admin.")
    exit(1)


threads = []
for user, (topic, messages) in zip(users, topics_messages.items()):
    token = register_or_login_user(user)
    if token:
        thread = threading.Thread(target=chat_session, args=(token, messages, topic))
        thread.start()
        threads.append(thread)
        time.sleep(2)

for thread in threads:
    thread.join()



