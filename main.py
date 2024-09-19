import serial
import binascii

def read_usb_data(port, baud_rate=9600):
    try:
        # 打开串口
        ser = serial.Serial(port, baud_rate, timeout=1)
        print(f"正在监听 {port}，波特率 {baud_rate}...")

        buffer = bytearray()  # 用于存储未处理的数据流

        while True:
            # 如果有数据等待读取
            if ser.in_waiting > 0:
                # 读取所有可用数据并添加到缓冲区
                buffer.extend(ser.read(ser.in_waiting))

                # 检查并处理小包
                while len(buffer) >= 8:  # 检查是否有完整的小包（8字节）
                    # 检查包头是否是 AA AA 04 80 02
                    if buffer[0:5] == b'\xAA\xAA\x04\x80\x02':
                        # 小包的格式为 8字节：AA AA 04 80 02 xxHigh xxLow xxCheckSum
                        packet = buffer[:8]  # 取出完整的8字节包
                        buffer = buffer[8:]  # 从缓冲区移除已处理的包
                        
                        # 打印接收到的完整小包
                        hex_data = binascii.hexlify(packet).decode('utf-8').upper()
                        print(f"接收到的小包: {hex_data}")
                    else:
                        break

                # 检查并处理大包
                while len(buffer) >= 36:  # 检查是否有完整的大包（36字节）
                    # 检查包头是否是 AA AA 并且包长度是 0x20（32字节 payload）
                    if buffer[0:2] == b'\xAA\xAA' and buffer[2] == 0x20:
                        # 大包的格式为 36字节：AA AA 20 (payload 32 bytes) CheckSum
                        packet = buffer[:36]  # 取出完整的36字节包
                        buffer = buffer[36:]  # 从缓冲区移除已处理的包
                        
                        # 打印接收到的完整大包
                        hex_data = binascii.hexlify(packet).decode('utf-8').upper()
                        print(f"接收到的大包: {hex_data}")
                    else:
                        break

    except serial.SerialException as e:
        print(f"错误: {e}")
    except KeyboardInterrupt:
        print("停止脚本...")

    finally:
        # 关闭串口
        if ser.is_open:
            ser.close()
        print("串口已关闭.")

if __name__ == "__main__":
    # 使用COM12端口，波特率9600
    read_usb_data('COM12', 9600)
