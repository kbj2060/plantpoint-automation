import paho.mqtt.client as mqtt

# 첫 번째 클라이언트
client1 = mqtt.Client(client_id="client_1")
client1.connect("mqtt.eclipseprojects.io", 1883, 60)

# 두 번째 클라이언트
client2 = mqtt.Client(client_id="client_2")
client2.connect("mqtt.eclipseprojects.io", 1883, 60)

# 연결 테스트
client1.loop_start()
client2.loop_start()

client1.publish("test/topic", "Message from client 1")
client2.publish("test/topic", "Message from client 2")

client1.loop_stop()
client2.loop_stop()

