# hand_swap.py
import cv2
import mediapipe as mp
import numpy as np
from collections import deque, Counter
import os

# Config Mediapipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)
mp_draw = mp.solutions.drawing_utils

# Rutas de imágenes 
IMG_FILES = {
    0: "seriedad.jpg",
    2: "okai.jpg",
    3: "kiubo.jpg",
    4: "haifour.jpg",
}

# Verificar y cargar imágenes
loaded_imgs = {}
for k, fn in IMG_FILES.items():
    if not os.path.exists(fn):
        print(f"ERROR: falta '{fn}' en la carpeta.")
        exit()
    img = cv2.imread(fn)
    if img is None:
        print(f"ERROR: no se pudo leer '{fn}'")
        exit()
    loaded_imgs[k] = img

DEFAULT_IMG = loaded_imgs[0]

# Conteo de dedos
def count_fingers(hand_landmarks):
    lm = hand_landmarks.landmark
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]

    count = 0
    for t, p in zip(tips, pips):
        if lm[t].y < lm[p].y - 0.02:
            count += 1

    wrist_x = lm[0].x
    index_mcp_x = lm[5].x
    thumb_tip_x = lm[4].x

    palm_direction_right = index_mcp_x > wrist_x

    if palm_direction_right:
        thumb_extended = thumb_tip_x > index_mcp_x + 0.03
    else:
        thumb_extended = thumb_tip_x < index_mcp_x - 0.03

    if thumb_extended:
        count += 1

    return max(0, min(5, count))

# Suavizado temporal
history = deque(maxlen=7)

def stable_count(new_val):
    if new_val is None:
        history.append(None)
    else:
        history.append(new_val)

    vals = [v for v in history if v is not None]
    if not vals:
        return 0

    return Counter(vals).most_common(1)[0][0]

# Cámara
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("ERROR: No se pudo abrir la cámara.")
    exit()

cv2.namedWindow("Hand Swap", cv2.WINDOW_NORMAL)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame_flipped = cv2.flip(frame, 1)
    h, w = frame_flipped.shape[:2]

    rgb = cv2.cvtColor(frame_flipped, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    detected = None

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame_flipped, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        try:
            detected = count_fingers(hand_landmarks)
        except:
            detected = None

    stable = stable_count(detected)

    if stable in loaded_imgs:
        selected_img = loaded_imgs[stable]
    else:
        selected_img = DEFAULT_IMG

    img_right = cv2.resize(selected_img, (w, h))

    combined = np.hstack((frame_flipped, img_right))

    cv2.rectangle(combined, (10,10), (330,60), (0,0,0), -1)
    text = f"Dedos (est): {stable}   Det: {detected}"
    cv2.putText(combined, text, (20,45), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

    cv2.imshow("Hand Swap", combined)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

hands.close()
cap.release()
cv2.destroyAllWindows()
