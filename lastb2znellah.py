import cv2 
import socket
import pyttsx3
import threading
from pyzbar.pyzbar import decode

# ESP32-CAM stream and UDP settings
ESP32_CAM_STREAM_URL = "http://192.168.43.52:81/stream"
UDP_IP = "192.168.43.82"
UDP_PORT = 5005

# Initialize UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Initialize video capture
cap = cv2.VideoCapture(ESP32_CAM_STREAM_URL)

# Initialize TTS engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)
for voice in engine.getProperty('voices'):
    if "female" in voice.name.lower() or "zira" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

# Function to handle TTS
def speak_name(name):
    engine.say(name)
    engine.runAndWait()

print("Press 'q' to quit.")
last_qr_data = ""
frame_skip = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame from ESP32-CAM.")
        continue

    frame_skip += 1
    if frame_skip % 5 != 0:
        continue

    decoded_objects = decode(frame)

    if decoded_objects:
        qr = decoded_objects[0]
        data = qr.data.decode("utf-8")

        if "MECARD:N:" in data:
            target_name = data.split("MECARD:N:")[1].rstrip(';')
        else:
            target_name = data.strip().rstrip(';')

        if target_name != last_qr_data:
            print(f"[QR Code Detected]: {target_name}")
            sock.sendto(target_name.encode(), (UDP_IP, UDP_PORT))
            last_qr_data = target_name
            threading.Thread(target=speak_name, args=(target_name,), daemon=True).start()

        # Draw bounding box
        pts = qr.polygon
        for i in range(len(pts)):
            pt1 = tuple(pts[i])
            pt2 = tuple(pts[(i + 1) % len(pts)])
            cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

        # Draw label
        cv2.putText(frame, target_name, (50, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (255, 0, 0), 2, cv2.LINE_AA)
    else:
        last_qr_data = ""

    cv2.imshow("ESP32-CAM QR Scanner", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
