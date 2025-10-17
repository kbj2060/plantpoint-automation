#!/usr/bin/env python3
"""
DHT22 센서 핀 자동 감지 및 GPIO 상태 확인 스크립트
"""

import time
import sys
import os
import subprocess

# Adafruit_DHT 라이브러리 import
try:
    import Adafruit_DHT
    DHT_AVAILABLE = True
except ImportError:
    print("❌ Adafruit_DHT 라이브러리를 찾을 수 없습니다.")
    sys.exit(1)

def check_gpio_status():
    """현재 GPIO 상태 확인"""
    print("🔍 현재 GPIO 상태 확인...")
    
    try:
        # gpio readall 명령어 실행 (wiringPi가 설치된 경우)
        result = subprocess.run(['gpio', 'readall'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("📊 GPIO 핀 상태:")
            print(result.stdout)
        else:
            print("⚠️ wiringPi가 설치되지 않았습니다.")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️ gpio 명령어를 사용할 수 없습니다.")
    
    # /sys/class/gpio에서 활성화된 핀 확인
    try:
        gpio_dir = "/sys/class/gpio"
        if os.path.exists(gpio_dir):
            exported_pins = []
            for item in os.listdir(gpio_dir):
                if item.startswith("gpio") and item != "gpiochip0":
                    pin_num = item.replace("gpio", "")
                    exported_pins.append(pin_num)
            
            if exported_pins:
                print(f"📌 현재 export된 GPIO 핀: {exported_pins}")
            else:
                print("📌 현재 export된 GPIO 핀이 없습니다.")
    except Exception as e:
        print(f"⚠️ GPIO 상태 확인 중 오류: {e}")

def test_dht22_comprehensive():
    """DHT22 센서를 모든 가능한 핀에서 테스트"""
    print("\n🌡️ DHT22 센서 포괄적 테스트 시작...")
    
    # 더 많은 핀을 테스트 (라즈베리파이에서 사용 가능한 핀들)
    test_pins = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
    
    found_sensors = []
    
    for pin in test_pins:
        print(f"🔍 GPIO {pin} 핀 테스트 중...", end=" ")
        
        try:
            # 더 많은 시도와 긴 대기 시간
            for attempt in range(5):
                humidity, temperature = Adafruit_DHT.read_retry(
                    Adafruit_DHT.DHT22, pin, retries=1, delay_seconds=0.5
                )
                
                if humidity is not None and temperature is not None:
                    # 유효한 값인지 확인
                    if 0 <= humidity <= 100 and -40 <= temperature <= 80:
                        found_sensors.append({
                            'pin': pin,
                            'temperature': temperature,
                            'humidity': humidity,
                            'attempt': attempt + 1
                        })
                        print(f"✅ 발견! (시도 {attempt + 1})")
                        break
                else:
                    time.sleep(0.1)
            else:
                print("❌")
                
        except Exception as e:
            print(f"❌ 오류: {e}")
        
        time.sleep(0.2)  # 핀 간 대기
    
    return found_sensors

def analyze_results(found_sensors):
    """테스트 결과 분석"""
    print(f"\n📊 테스트 결과 분석:")
    print(f"총 {len(found_sensors)}개의 핀에서 DHT22 센서 발견")
    
    if not found_sensors:
        print("\n❌ DHT22 센서를 찾을 수 없습니다.")
        print("\n💡 해결 방법:")
        print("1. DHT22 센서 연결 확인:")
        print("   - VCC → 3.3V 또는 5V")
        print("   - GND → Ground")
        print("   - DATA → GPIO 핀")
        print("2. 센서가 손상되지 않았는지 확인")
        print("3. 다른 DHT22 센서로 테스트")
        return None
    
    # 가장 안정적인 센서 찾기 (여러 시도에서 일관된 값)
    best_sensor = None
    for sensor in found_sensors:
        if sensor['attempt'] == 1:  # 첫 시도에서 성공
            best_sensor = sensor
            break
    
    if not best_sensor:
        best_sensor = found_sensors[0]  # 첫 번째 발견된 센서
    
    print(f"\n🎯 추천 핀: GPIO {best_sensor['pin']}")
    print(f"   온도: {best_sensor['temperature']:.1f}°C")
    print(f"   습도: {best_sensor['humidity']:.1f}%")
    print(f"   안정성: {'높음' if best_sensor['attempt'] == 1 else '보통'}")
    
    # 모든 발견된 센서 표시
    if len(found_sensors) > 1:
        print(f"\n📋 발견된 모든 센서:")
        for i, sensor in enumerate(found_sensors, 1):
            print(f"   {i}. GPIO {sensor['pin']}: "
                  f"{sensor['temperature']:.1f}°C, "
                  f"{sensor['humidity']:.1f}%")
    
    return best_sensor

def monitor_sensor(pin, duration=30):
    """특정 핀에서 센서 모니터링"""
    print(f"\n📈 GPIO {pin} 핀에서 {duration}초간 모니터링...")
    print("Ctrl+C로 중지 가능")
    
    start_time = time.time()
    readings = []
    
    try:
        while time.time() - start_time < duration:
            humidity, temperature = Adafruit_DHT.read_retry(
                Adafruit_DHT.DHT22, pin, retries=1, delay_seconds=0.5
            )
            
            if humidity is not None and temperature is not None:
                readings.append((temperature, humidity))
                current_time = time.strftime("%H:%M:%S")
                
                # 값의 안정성 표시
                if len(readings) > 1:
                    temp_diff = abs(temperature - readings[-2][0])
                    hum_diff = abs(humidity - readings[-2][1])
                    stability = "안정" if temp_diff < 1 and hum_diff < 2 else "변동"
                else:
                    stability = "초기"
                
                print(f"[{current_time}] 온도: {temperature:5.1f}°C, "
                      f"습도: {humidity:5.1f}% ({stability})")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] ❌ 읽기 실패")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n⏹️ 모니터링 중지됨")
    
    # 통계 출력
    if readings:
        temps = [r[0] for r in readings]
        hums = [r[1] for r in readings]
        
        print(f"\n📊 통계 (총 {len(readings)}회 측정):")
        print(f"   온도: 평균 {sum(temps)/len(temps):.1f}°C, "
              f"범위 {min(temps):.1f}~{max(temps):.1f}°C")
        print(f"   습도: 평균 {sum(hums)/len(hums):.1f}%, "
              f"범위 {min(hums):.1f}~{max(hums):.1f}%")

def main():
    """메인 함수"""
    print("🔍 DHT22 센서 핀 자동 감지 도구")
    print("=" * 50)
    
    # 1. 현재 GPIO 상태 확인
    check_gpio_status()
    
    # 2. DHT22 센서 검색
    found_sensors = test_dht22_comprehensive()
    
    # 3. 결과 분석
    best_sensor = analyze_results(found_sensors)
    
    if best_sensor:
        # 4. 모니터링 여부 확인
        try:
            response = input(f"\nGPIO {best_sensor['pin']} 핀에서 모니터링을 시작하시겠습니까? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                monitor_sensor(best_sensor['pin'], 30)
        except KeyboardInterrupt:
            print("\n👋 프로그램을 종료합니다.")
        
        print(f"\n📝 코드 설정:")
        print(f"   DHT_PIN = {best_sensor['pin']}")

if __name__ == "__main__":
    main()
