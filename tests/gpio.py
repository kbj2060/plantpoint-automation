from constants import USE_REAL_GPIO

if not USE_REAL_GPIO:
    from fake_rpi.RPi import GPIO
else:
    import RPi.GPIO as GPIO
    
import time

# GPIO 모드 설정 (BCM 또는 BOARD)
GPIO.setmode(GPIO.BCM)

# 출력 핀과 입력 핀 목록
output_pins = [26, 19, 13]  # 출력 핀 번호
input_pins = [20, 16,21]
#common_pins = set(output_pins) & set(input_pins)
#input_pins = list(set(input_pins) - common_pins)
#print(input_pins)

# 출력 핀 설정
for pin in output_pins:
    GPIO.setup(pin, GPIO.OUT)  # 출력 핀 설정
    GPIO.output(pin, GPIO.LOW)  # 초기 상태를 LOW로 설정 (꺼짐)

# 입력 핀 설정
for pin in input_pins:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # 풀다운 저항 활성화

# 출력 핀 제어 및 입력 핀 읽기
try:
    while True:
        # 출력 핀 순차적으로 켜고 끄기
        for pPin in output_pins:
            GPIO.output(pPin, GPIO.HIGH)  # 출력 핀 켜기

            for iPin in input_pins:
                if GPIO.input(iPin) == GPIO.HIGH:  # 입력 핀이 활성화되었는지 확인
                    print(f"INPUT PIN {iPin} /  OUTPUT PIN {pPin} ")

            time.sleep(5)  # 1초 대기
            GPIO.output(pPin, GPIO.LOW)  # 출력 핀 끄기

except KeyboardInterrupt:
    print("Program stopped by user")

finally:
    GPIO.cleanup()  # GPIO 설정 초기화

