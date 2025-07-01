# UDP JPEG streaming + steering 전송 통합 예제
import cv2
import mediapipe as mp
import numpy as np
from udp_sender import send_steering, send_image

# Mediapipe 초기화
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2,
                       min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture("src/hand_simulator/test.mp4")

frame_idx = 0
steering_value = 0.0
steering_ema = 0.0
last_direction = "NEUTRAL"
alpha = 0.2
ema_alpha = 0.1


def get_direction_from_y_axis(hand_info):
    if 'Left' in hand_info and 'Right' in hand_info:
        left_y = hand_info['Left'].landmark[0].y
        right_y = hand_info['Right'].landmark[0].y
        threshold = 0.17
        if left_y + threshold < right_y:
            return "LEFT TURN"
        elif right_y + threshold < left_y:
            return "RIGHT TURN"
        else:
            return "NEUTRAL"
    return "NONE"

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    image = cv2.flip(frame, 1)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    direction_result = "NONE"

    if results.multi_hand_landmarks and results.multi_handedness:
        h, w, _ = image.shape
        hand_info = {}

        for handedness, landmarks in zip(results.multi_handedness, results.multi_hand_landmarks):
            label = handedness.classification[0].label
            hand_info[label] = landmarks
            mp_drawing.draw_landmarks(image, landmarks, mp_hands.HAND_CONNECTIONS)

        direction_result = get_direction_from_y_axis(hand_info)

        if direction_result in ["LEFT TURN", "RIGHT TURN", "NEUTRAL"]:
            last_direction = direction_result
            if direction_result == "LEFT TURN":
                steering_value = -1.0
            elif direction_result == "RIGHT TURN":
                steering_value = 1.0
            else:
                steering_value = 0.0

    if direction_result == "NONE":
        steering_value *= (1 - alpha)

    # EMA Smoothing
    steering_ema = ema_alpha * steering_value + (1 - ema_alpha) * steering_ema

    # 시각화 텍스트 포함
    cv2.putText(image, f"{last_direction} | Steering: {steering_ema:.2f}",
                (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

    # 전송용 JPEG 압축
    _, jpeg_img = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 60])
    img_bytes = jpeg_img.tobytes()

    # 영상 전송
    send_image(img_bytes)

    # 조향 값도 별도 전송
    send_steering(steering_ema)

    cv2.imshow("Streaming View", image)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
