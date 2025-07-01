import socket

def send_steering(steering_ema):
    # UDP 전송 설정
    UDP_IP = "127.0.0.1"     # Unreal Engine이 실행되는 IP , Config로 분리
    UDP_PORT = 5005          # Unreal에서 수신할 포트
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # steering_smooth 전송 코드 (while 루프 내에 추가)
    msg = f"{steering_ema:.4f}"
    sock.sendto(msg.encode(), (UDP_IP, UDP_PORT))
    print(f"Sent: {msg}")

def send_image(image_byte):
    # UDP 전송 세팅
    IMG_UDP_IP = '127.0.0.1'
    IMG_UDP_PORT = 10000
    img_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 길이 체크 및 UDP 전송 (단순 최대 60KB 내로 제한)
    if len(image_byte) < 60000:
        img_sock.sendto(image_byte, (IMG_UDP_IP, IMG_UDP_PORT))