#!/usr/bin/env python3
"""
DHT22 센서 테스트 및 핀 자동 검색 스크립트

이 스크립트는 DHT22 센서가 연결된 GPIO 핀을 자동으로 찾고
온도와 습도를 측정하여 출력합니다.
"""

import time
import sys
import os

# Adafruit_DHT 라이브러리 import
try:
    import Adafruit_DHT
    DHT_AVAILABLE = True
    print("✅ Adafruit_DHT 라이브러리 로드 성공")
except ImportError:
    print("❌ Adafruit_DHT 라이브러리를 찾을 수 없습니다.")
    print("설치 방법: pip install Adafruit-DHT")
    sys.exit(1)

# 테스트할 GPIO 핀 목록 (라즈베리파이에서 일반적으로 사용되는 핀들)
TEST_PINS = [4, 17, 18, 22, 23, 24, 25, 27]

def test_dht22_on_pin(pin):
    """
    특정 핀에서 DHT22 센서 테스트
    
    Args:
        pin (int): 테스트할 GPIO 핀 번호
        
    Returns:
        tuple: (성공여부, 온도, 습도) 또는 (False, None, None)
    """
    try:
        print(f"🔍 GPIO {pin} 핀에서 DHT22 센서 검색 중...")
        
        # DHT22 센서 읽기 (최대 3번 시도)
        for attempt in range(3):
            humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, pin)
            
            if humidity is not None and temperature is not None:
                print(f"✅ GPIO {pin} 핀에서 DHT22 센서 발견!")
                print(f"   온도: {temperature:.1f}°C")
                print(f"   습도: {humidity:.1f}%")
                return True, temperature, humidity
            else:
                print(f"   시도 {attempt + 1}/3 실패")
                time.sleep(1)
        
        print(f"❌ GPIO {pin} 핀에서 DHT22 센서를 찾을 수 없음")
        return False, None, None
        
    except Exception as e:
        print(f"❌ GPIO {pin} 핀 테스트 중 오류: {e}")
        return False, None, None

def find_dht22_sensor():
    """
    모든 가능한 핀에서 DHT22 센서를 찾기
    
    Returns:
        tuple: (발견된 핀 번호, 온도, 습도) 또는 (None, None, None)
    """
    print("🔍 DHT22 센서 자동 검색 시작...")
    print(f"테스트할 핀: {TEST_PINS}")
    print("-" * 50)
    
    for pin in TEST_PINS:
        success, temp, humidity = test_dht22_on_pin(pin)
        if success:
            return pin, temp, humidity
        time.sleep(0.5)  # 핀 간 대기
    
    print("❌ 모든 핀에서 DHT22 센서를 찾을 수 없습니다.")
    return None, None, None

def continuous_monitoring(pin, duration=60):
    """
    특정 핀에서 연속 모니터링
    
    Args:
        pin (int): DHT22가 연결된 GPIO 핀 번호
        duration (int): 모니터링 시간 (초)
    """
    print(f"\n📊 GPIO {pin} 핀에서 {duration}초간 연속 모니터링 시작...")
    print("Ctrl+C를 눌러 중지할 수 있습니다.")
    print("-" * 50)
    
    start_time = time.time()
    reading_count = 0
    
    try:
        while time.time() - start_time < duration:
            humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, pin)
            
            if humidity is not None and temperature is not None:
                reading_count += 1
                current_time = time.strftime("%H:%M:%S")
                
                # 상태 표시
                temp_status = "✅" if 15 <= temperature <= 35 else "⚠️"
                humidity_status = "✅" if 30 <= humidity <= 90 else "⚠️"
                
                print(f"[{current_time}] #{reading_count:03d} | "
                      f"온도: {temperature:5.1f}°C {temp_status} | "
                      f"습도: {humidity:5.1f}% {humidity_status}")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] ❌ 센서 읽기 실패")
            
            time.sleep(2)  # 2초 간격으로 읽기
            
    except KeyboardInterrupt:
        print(f"\n⏹️  모니터링 중지됨 (총 {reading_count}회 읽기 완료)")
    except Exception as e:
        print(f"\n❌ 모니터링 중 오류: {e}")

def main():
    """메인 함수"""
    print("🌡️  DHT22 센서 테스트 및 핀 검색 도구")
    print("=" * 50)
    
    # 1. 센서 자동 검색
    pin, temp, humidity = find_dht22_sensor()
    
    if pin is None:
        print("\n💡 해결 방법:")
        print("1. DHT22 센서가 올바르게 연결되었는지 확인")
        print("2. VCC(3.3V), GND, DATA 핀 연결 확인")
        print("3. 다른 핀 번호를 수동으로 테스트")
        return
    
    print(f"\n🎉 DHT22 센서를 GPIO {pin} 핀에서 발견했습니다!")
    print(f"   최초 측정값 - 온도: {temp:.1f}°C, 습도: {humidity:.1f}%")
    
    # 2. 연속 모니터링 여부 확인
    try:
        response = input("\n연속 모니터링을 시작하시겠습니까? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            continuous_monitoring(pin, 60)
    except KeyboardInterrupt:
        print("\n👋 프로그램을 종료합니다.")
    
    print(f"\n📝 사용법:")
    print(f"   코드에서 DHT_PIN = {pin} 으로 설정하세요")
    print(f"   예: DHT_PIN = {pin}")

if __name__ == "__main__":
    main()
