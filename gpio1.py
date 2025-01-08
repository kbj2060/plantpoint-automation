import RPi.GPIO as GPIO
import time

# GPIO 핀 번호 설정 (BCM 모드 사용)
GPIO.setmode(GPIO.BCM)

# 입력 핀 번호 정의 (예: GPIO 17, GPIO 27)
input_pins = [4, 21, 20, 8,6, 7,9,16,3]

# 핀을 입력 모드로 설정
for pin in input_pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # 풀다운

try:
    while True:
        for pin in input_pins:
            state = GPIO.input(pin)  # HIGH(1) 또는 LOW(0) 확인
            if state == GPIO.HIGH:
                print(f"Pin {pin}: HIGH")
            else:
                print(f"Pin {pin}: LOW")
        time.sleep(1)  # 1초 대기

except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()  # GPIO 설정 정리

