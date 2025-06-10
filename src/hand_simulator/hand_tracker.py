import cv2
import mediapipe as mp
import numpy as np
import pandas as pd

# Mediapipe 초기화
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2,
                       min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture("src/hand_simulator/test.mp4")

frame_idx = 0
steering_log = []

# 지속 입력을 위한 상태 변수
last_direction = "NEUTRAL"
steering_value = 0.0  # -1.0: left, 0: neutral, +1.0: right
alpha = 0.2  # 감쇠율

# ✅ Y축 기준 조향 판단 함수
def get_direction_from_y_axis(hand_info):
    """
    Determine steering direction based on vertical Y position of wrists.
    Y: 0 (top of image) to 1 (bottom of image)
    """
    if 'Left' in hand_info and 'Right' in hand_info:
        left_y = hand_info['Left'].landmark[0].y
        right_y = hand_info['Right'].landmark[0].y

        threshold = 0.17  # 민감도

        if left_y + threshold < right_y:
            return "LEFT TURN"
        elif right_y + threshold < left_y:
            return "RIGHT TURN"
        else:
            return "NEUTRAL"
    return "NONE"

# 방향 안정화 함수
def stabilize_directions(directions, min_consistent_frames=3):
    stable_directions = []
    current = directions[0]
    temp = current
    count = 1

    for i in range(1, len(directions)):
        if directions[i] == temp:
            count += 1
        else:
            temp = directions[i]
            count = 1

        if count >= min_consistent_frames:
            current = temp
        stable_directions.append(current)

    return [directions[0]] + stable_directions

# 메인 루프
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

    # 손이 감지되지 않거나 "NONE"일 때는 서서히 감쇠
    if direction_result == "NONE":
        steering_value *= (1 - alpha)

    # 시각화
    cv2.putText(image, f"{last_direction} | Steering: {steering_value:.2f}",
                (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

    # 로그 저장
    steering_log.append({
        "frame": frame_idx,
        "direction": last_direction,
        "steering": steering_value
    })
    frame_idx += 1

    cv2.imshow("Y-Axis Steering", image)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

# CSV 저장
df = pd.DataFrame(steering_log)
df["stable_direction"] = stabilize_directions(df["direction"].tolist())
df.to_csv("y_axis_steering.csv", index=False)
print("조향 결과가 'y_axis_steering.csv'에 저장되었습니다.")
