import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import serial
import threading
import binascii
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class SerialApp:
    def __init__(self, root):
        self.root = root
        self.root.title("脑波数据接收器和可视化工具")
        self.serial_port = None
        self.baud_rate = 9600
        self.is_serial_open = False
        self.buffer = bytearray()

        # 数据存储
        self.raw_data = []
        self.eeg_powers = {
            "Delta": [], "Theta": [], "LowAlpha": [], "HighAlpha": [],
            "LowBeta": [], "HighBeta": [], "LowGamma": [], "MiddleGamma": []
        }
        self.attention = []
        self.meditation = []

        # 创建主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧数据输出框（使用scrolledtext替代text）
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.text_output = scrolledtext.ScrolledText(left_frame, height=20, width=60)
        self.text_output.pack(fill=tk.BOTH, expand=True)

        # 右侧功能按钮
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # 打开串口按钮
        self.open_button = tk.Button(right_frame, text="打开串口", command=self.open_serial)
        self.open_button.pack(pady=5)

        # 关闭串口按钮
        self.close_button = tk.Button(right_frame, text="关闭串口", command=self.close_serial, state=tk.DISABLED)
        self.close_button.pack(pady=5)

        # 设置波特率输入框和按钮
        tk.Label(right_frame, text="波特率:").pack()
        self.baud_entry = tk.Entry(right_frame)
        self.baud_entry.insert(0, "9600")  # 默认波特率
        self.baud_entry.pack(pady=5)

        self.set_baud_button = tk.Button(right_frame, text="设置波特率", command=self.set_baud_rate)
        self.set_baud_button.pack(pady=5)

        # 清空窗口按钮
        self.clear_button = tk.Button(right_frame, text="清空窗口", command=self.clear_output)
        self.clear_button.pack(pady=5)

        # 保存窗口内容到文件按钮
        self.save_button = tk.Button(right_frame, text="保存到文件", command=self.save_to_file)
        self.save_button.pack(pady=5)

        # 创建图表
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.line, = self.ax.plot([], [])
        self.ax.set_ylim(-500, 500)  # 根据实际数据范围调整
        self.ax.set_title("Raw EEG Data")
        self.ax.set_xlabel("Samples")
        self.ax.set_ylabel("Amplitude")

        tk.Label(self.root, text="脑波哨兵 All Rights Reserved © 2024", font=("黑体", 8)).pack(pady=5)

        # 设置定期更新图表的任务
        self.root.after(100, self.update_plot)

    # 打开串口
    def open_serial(self):
        try:
            port = 'COM12'  # 这里可以设置端口号
            self.serial_port = serial.Serial(port, self.baud_rate, timeout=1)
            self.is_serial_open = True
            self.open_button.config(state=tk.DISABLED)
            self.close_button.config(state=tk.NORMAL)
            self.text_output.insert(tk.END, f"串口 {port} 已打开，波特率为 {self.baud_rate}\n")
            self.read_serial_data()  # 启动串口数据读取线程
        except serial.SerialException as e:
            messagebox.showerror("错误", f"无法打开串口: {e}")

    # 关闭串口
    def close_serial(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.is_serial_open = False
        self.open_button.config(state=tk.NORMAL)
        self.close_button.config(state=tk.DISABLED)
        self.text_output.insert(tk.END, "串口已关闭\n")

    # 设置波特率
    def set_baud_rate(self):
        try:
            baud_rate = int(self.baud_entry.get())
            self.baud_rate = baud_rate
            self.text_output.insert(tk.END, f"波特率设置为: {baud_rate}\n")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的波特率数字")

    # 清空输出窗口
    def clear_output(self):
        self.text_output.delete(1.0, tk.END)

    # 保存输出到txt文件
    def save_to_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, "w") as f:
                f.write(self.text_output.get(1.0, tk.END))
            messagebox.showinfo("保存成功", f"数据已保存到 {file_path}")

    # 校验和计算
    def calculate_checksum(self, data):
        checksum = (0x80 + 0x02 + data[5] + data[6]) & 0xFFFFFFFF
        return (~checksum) & 0xFF  # 取反并取低8位

    # 解析小包
    def parse_small_packet(self, packet):
        xx_high = packet[5]
        xx_low = packet[6]
        xx_checksum = packet[7]
        calculated_checksum = self.calculate_checksum(packet)

        hex_data = binascii.hexlify(packet).decode('utf-8').upper()
        self.text_output.insert(tk.END, f"接收到的小包: {hex_data}\n")

        if calculated_checksum == xx_checksum:
            rawdata = (xx_high << 8) | xx_low
            if rawdata > 32768:
                rawdata -= 65536
            self.raw_data.append(rawdata)
            result = f"原始数据: {rawdata}"
            self.text_output.insert(tk.END, f"小包解析结果: {result}\n")
        else:
            self.text_output.insert(tk.END, "校验和不匹配，忽略此小包\n")
        
        self.text_output.see(tk.END)  # 自动滚动到最新内容

    # 解析大包
    def parse_large_packet(self, packet):
        if len(packet) != 36:
            self.text_output.insert(tk.END, f"接收到的大包长度不正确 (长度: {len(packet)}), 忽略此包\n")
            return

        hex_data = binascii.hexlify(packet).decode('utf-8').upper()
        self.text_output.insert(tk.END, f"接收到的大包: {hex_data}\n")

        signal_value = packet[4]
        result = [f"信号强度 (Signal): {signal_value}"]

        eeg_power_labels = ["Delta", "Theta", "LowAlpha", "HighAlpha", "LowBeta", "HighBeta", "LowGamma", "MiddleGamma"]
        eeg_powers = {}

        for i, label in enumerate(eeg_power_labels):
            start_index = 7 + i * 3
            value = (packet[start_index] << 16) | (packet[start_index + 1] << 8) | packet[start_index + 2]
            eeg_powers[label] = value
            self.eeg_powers[label].append(value)
            result.append(f"{label}: {value}")

        attention_value = packet[32]
        meditation_value = packet[34]
        self.attention.append(attention_value)
        self.meditation.append(meditation_value)
        result.append(f"专注度 (Attention): {attention_value}")
        result.append(f"放松度 (Meditation): {meditation_value}")

        for line in result:
            self.text_output.insert(tk.END, f"{line}\n")

        self.text_output.see(tk.END)  # 自动滚动到最新内容
        
    # 读取串口数据
    def read_serial_data(self):
        def read():
            while self.is_serial_open:
                if self.serial_port.in_waiting > 0:
                    try:
                        new_data = self.serial_port.read(self.serial_port.in_waiting)
                        self.buffer.extend(new_data)

                        # 处理包
                        while len(self.buffer) >= 8:
                            if self.buffer[0:5] == b'\xAA\xAA\x04\x80\x02':
                                if len(self.buffer) >= 8:
                                    packet = self.buffer[:8]
                                    self.buffer = self.buffer[8:]
                                    self.parse_small_packet(packet)
                                else:
                                    break  # 等待更多数据
                            elif self.buffer[0:3] == b'\xAA\xAA\x20':
                                if len(self.buffer) >= 36:
                                    packet = self.buffer[:36]
                                    self.buffer = self.buffer[36:]
                                    self.parse_large_packet(packet)
                                else:
                                    break  # 等待更多数据
                            else:
                                self.buffer = self.buffer[1:]

                    except serial.SerialException as e:
                        self.text_output.insert(tk.END, f"读取错误: {e}\n")
                        self.is_serial_open = False
                        break

        threading.Thread(target=read, daemon=True).start()

    # 更新图表
    def update_plot(self):
        if len(self.raw_data) > 1024:  # 只显示最近的1024个数据点
            self.raw_data = self.raw_data[-1024:]
        
        self.line.set_data(range(len(self.raw_data)), self.raw_data)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

        # 安排下一次更新
        self.root.after(100, self.update_plot)

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialApp(root)
    root.mainloop()