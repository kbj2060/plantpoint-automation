-- 1. automation_type 테이블에 데이터 삽입
INSERT INTO automation_type (id, name) VALUES
(1, 'interval'),
(2, 'range'),
(3, 'target')
ON CONFLICT (id) DO NOTHING;

-- 6. environment_type 테이블에 데이터 삽입
INSERT INTO environment_type (id, name, unit, description) VALUES
(1, 'temperature', '°C', '온도 측정'),
(2, 'humidity', '%', '습도 측정'),
(3, 'ph', 'pH', '수소이온농도'),
(4, 'ec', 'mS/cm', '전기전도도'),
(5, 'co2', 'ppm', '이산화탄소 농도'),
(6, 'water_temperature', '°C', '수온 측정')
ON CONFLICT (id) DO NOTHING;

-- 2. device 테이블에 데이터 삽입
INSERT INTO device (id, name, type, automation_type_id, pin) VALUES
(1, 'led', 'machine', 2, 1),              -- range 타입
(2, 'waterspray', 'machine', 1, 2),        -- interval 타입
(3, 'fan', 'machine', 1, 3),              -- interval 타입
(4, 'airconditioner', 'machine', 3, 4),    -- target 타입
(5, 'ph', 'sensor', 3, 6)                -- target 타입
ON CONFLICT (id) DO NOTHING;

-- 3. interval_automation 테이블에 데이터 삽입
INSERT INTO interval_automation (device_id, interval, duration, active) VALUES
(2, '10m', '10s', true),    -- waterspray
(3, '60m', '60m', true)  -- fan
ON CONFLICT (device_id) DO UPDATE SET
  interval = EXCLUDED.interval,
  duration = EXCLUDED.duration,
  active = EXCLUDED.active;

-- 4. range_automation 테이블에 데이터 삽입
INSERT INTO range_automation (device_id, start_time, end_time, active) VALUES
(1, '06:00', '18:00', true)  -- led
ON CONFLICT (device_id) DO UPDATE SET
  start_time = EXCLUDED.start_time,
  end_time = EXCLUDED.end_time,
  active = EXCLUDED.active;

-- 5. target_automation 테이블에 데이터 삽입
INSERT INTO target_automation (device_id, target, margin, active) VALUES
(4, 25, 1, true),  -- airconditioner
(5, 7, 1, true)   -- ph
ON CONFLICT (device_id) DO UPDATE SET
  target = EXCLUDED.target,
  margin = EXCLUDED.margin,
  active = EXCLUDED.active;

-- 7. environment_logs 테이블에 데이터 삽입 (기존 데이터 유지)
INSERT INTO environment_logs (environment_type, value, recorded_at) VALUES
(1, 25.5, CURRENT_TIMESTAMP),
(1, 26.0, CURRENT_TIMESTAMP),
(2, 65.0, CURRENT_TIMESTAMP),
(2, 67.0, CURRENT_TIMESTAMP),
(3, 6.5, CURRENT_TIMESTAMP);

-- 8. report 테이블에 데이터 삽입 (기존 데이터 유지)
INSERT INTO report (level, problem, is_fixed, created_at) VALUES
(1, '온도가 너무 높습니다', false, CURRENT_TIMESTAMP),
(2, '습도가 너무 낮습니다', true, CURRENT_TIMESTAMP),
(3, 'pH 값이 비정상입니다', false, CURRENT_TIMESTAMP),
(1, 'CO2 농도가 높습니다', false, CURRENT_TIMESTAMP),
(2, 'EC 값이 비정상입니다', true, CURRENT_TIMESTAMP);

-- 9. switches 테이블에 데이터 삽입 (마지막 상태만 삽입)
INSERT INTO switches (device_id, status, controlled_by, created_at) VALUES
(1, true, NULL, CURRENT_TIMESTAMP),
(2, false, 1, CURRENT_TIMESTAMP),
(3, true, 1, CURRENT_TIMESTAMP),
(4, false, NULL, CURRENT_TIMESTAMP),
(5, true, NULL, CURRENT_TIMESTAMP);
