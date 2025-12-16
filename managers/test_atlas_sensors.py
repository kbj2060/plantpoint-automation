import time
import sys
import os

# Add current directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.dirname(current_dir))

try:
    from drivers.AtlasI2C import AtlasI2C
except ImportError:
    print("Error: Could not import AtlasI2C driver.")
    print("Please ensure this script is in the 'plantpoint-automation' directory.")
    sys.exit(1)

def get_sensor_name(moduletype):
    mapping = {
        "RTD": "Water Temperature",
        "PH": "pH",
        "EC": "EC"
    }
    return mapping.get(moduletype.upper(), moduletype)

def main():
    print("=== Atlas Scientific I2C Sensor Test ===")
    
    # 1. Discover devices
    try:
        device = AtlasI2C()
        device_address_list = device.list_i2c_devices()
    except Exception as e:
        print(f"Error accessing I2C: {e}")
        return

    if not device_address_list:
        print("No Atlas I2C devices found.")
        return

    print(f"Found {len(device_address_list)} devices.")
    
    atlas_devices = []

    # 2. Initialize devices
    for address in device_address_list:
        try:
            device.set_i2c_address(address)
            response = device.query("I")
            # Response format example: "?I,RTD,1.0"
            parts = response.split(",")
            moduletype = parts[1] if len(parts) > 1 else "UNKNOWN"
            
            # Try to get name, but fallback if fails
            try:
                name_response = device.query("name,?")
                name = name_response.split(",")[1]
            except:
                name = moduletype

            atlas_device = AtlasI2C(address=address, moduletype=moduletype, name=name)
            atlas_devices.append(atlas_device)
            print(f"Initialized {moduletype} (Address: {address})")
        except Exception as e:
            print(f"Error initializing device at {address}: {e}")

    # 3. Read sensors
    print("\n--- Reading Sensor Values ---")
    for dev in atlas_devices:
        try:
            sensor_name = get_sensor_name(dev.moduletype)
            print(f"\nTesting {sensor_name} (Address: {dev.address})...")

            # Info
            print(f"  Info: {dev.query('I')}")
            
            # Status
            print(f"  Status: {dev.query('Status')}")

            # Read
            print("  Reading value...")
            dev.write("R")
            time.sleep(AtlasI2C.LONG_TIMEOUT)
            response = dev.read()
            print(f"  Result: {response}")

        except Exception as e:
            print(f"  Error testing sensor: {e}")

    print("\n=== Test Finished ===")

if __name__ == "__main__":
    main()