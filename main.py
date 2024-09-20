from collections import deque
import csv
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import serial
import threading
import binascii
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import serial.tools.list_ports
# 主应用程序类
class SerialApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EEG接收器和可视化工具V1.0")
        self.serial_port = None
        self.baud_rate = 9600
        self.is_serial_open = False
        self.buffer = bytearray()
        # 添加绘图开关变量
        self.plot_enabled = tk.BooleanVar(value=True)

        # 使用 deque 来存储数据，限制最大长度
        self.max_data_points = 1000
        self.raw_data = deque(maxlen=32767)
        self.eeg_powers = {
            "Delta": deque(maxlen=self.max_data_points), 
            "Theta": deque(maxlen=self.max_data_points), 
            "LowAlpha": deque(maxlen=self.max_data_points), 
            "HighAlpha": deque(maxlen=self.max_data_points),
            "LowBeta": deque(maxlen=self.max_data_points), 
            "HighBeta": deque(maxlen=self.max_data_points), 
            "LowGamma": deque(maxlen=self.max_data_points), 
            "MiddleGamma": deque(maxlen=self.max_data_points)
        }
        self.attention = deque(maxlen=self.max_data_points)
        self.meditation = deque(maxlen=self.max_data_points)

        self.create_main_frame()
        self.create_menu()
        self.create_status_bar()
        root.geometry("775x926")

        # 设置不同图表的更新间隔（毫秒）
        self.raw_eeg_update_interval = 100
        self.other_charts_update_interval = 1000
        self.last_raw_eeg_update = 0
        self.last_other_charts_update = 0
        # 设置定期更新图表的任务
        self.root.after(100, self.update_plots)  # 使用较短的间隔来检查更新

    def create_main_frame(self):
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧面板：控制和数据输出
        left_panel = ttk.Frame(main_frame)
        main_frame.add(left_panel, weight=1)

        # 控制面板
        control_frame = ttk.LabelFrame(left_panel, text="控制面板")
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # 串口选择和波特率设置
        ttk.Label(control_frame, text="选择串口:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.port_combobox = ttk.Combobox(control_frame, values=self.get_serial_ports())
        self.port_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(control_frame, text="波特率:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.baud_entry = ttk.Entry(control_frame)
        self.baud_entry.insert(0, "9600")
        self.baud_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # 添加绘图开关复选框
        self.plot_checkbox = ttk.Checkbutton(control_frame, text="启用绘图", variable=self.plot_enabled)
        self.plot_checkbox.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # 按钮布局
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=5)

        self.open_button = ttk.Button(button_frame, text="打开串口", command=self.open_serial)
        self.open_button.pack(side=tk.LEFT, padx=5)

        self.close_button = ttk.Button(button_frame, text="关闭串口", command=self.close_serial, state=tk.DISABLED)
        self.close_button.pack(side=tk.LEFT, padx=5)

        self.set_baud_button = ttk.Button(button_frame, text="设置波特率", command=self.set_baud_rate)
        self.set_baud_button.pack(side=tk.LEFT, padx=5)

        # 创建9个文本框用于显示数据
        self.data_frames = {}
        data_names = ["原始数据"] + list(self.eeg_powers.keys())
        for i, name in enumerate(data_names):
            frame = ttk.LabelFrame(left_panel, text=name)
            frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            text = scrolledtext.ScrolledText(frame, height=3)
            text.pack(fill=tk.BOTH, expand=True)
            self.data_frames[name] = text

        # 右侧面板：图表
        right_panel = ttk.Frame(main_frame)
        main_frame.add(right_panel, weight=2)

        # 调整图表大小以适配低分辨率
        self.fig, self.axs = plt.subplots(3, 1, figsize=(6, 8), dpi=100)  # 缩小figsize
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.setup_plots()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出数据", command=self.export_data)
        file_menu.add_command(label="退出", command=self.root.quit)

    def create_status_bar(self):
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_plots(self):
        self.raw_line, = self.axs[0].plot([], [])
        self.axs[0].set_ylim(-500, 500)
        self.axs[0].set_title("Raw EEG Data")
        self.axs[0].set_xlabel("Samples")
        self.axs[0].set_ylabel("Amplitude")

        x = range(len(self.eeg_powers))
        self.power_bars = self.axs[1].bar(x, [0] * len(self.eeg_powers))
        self.axs[1].set_title("EEG Power Bands")
        self.axs[1].set_xticks(x)
        self.axs[1].set_ylim(0, 5000)
        self.axs[1].set_xticklabels(self.eeg_powers.keys(), rotation=45)
        self.axs[1].set_ylabel("Power")

        self.attention_line, = self.axs[2].plot([], [], label='Attention')
        self.meditation_line, = self.axs[2].plot([], [], label='Meditation')
        self.axs[2].set_ylim(0, 100)
        self.axs[2].set_title("Attention and Meditation")
        self.axs[2].set_xlabel("Time")
        self.axs[2].set_ylabel("Level")
        self.axs[2].legend()

        self.fig.tight_layout()   

    #获取可用串口
    def get_serial_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]
    # 打开串口
    def open_serial(self):
        try:
            port = self.port_combobox.get()
            self.serial_port = serial.Serial(port, self.baud_rate, timeout=1)
            self.is_serial_open = True
            self.open_button.config(state=tk.DISABLED)
            self.close_button.config(state=tk.NORMAL)
            self.status_bar.config(text=f"已连接到 {port}")
            self.read_serial_data()
        except serial.SerialException as e:
            messagebox.showerror("错误", f"无法打开串口: {e}")

    # 关闭串口
    def close_serial(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.is_serial_open = False
        self.open_button.config(state=tk.NORMAL)
        self.close_button.config(state=tk.DISABLED)
        self.status_bar.config(text="未连接")

    # 设置波特率
    def set_baud_rate(self):
        try:
            self.baud_rate = int(self.baud_entry.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的波特率数字")

    # 校验和计算
    def calculate_checksum(self, data):
        checksum = (0x80 + 0x02 + data[5] + data[6]) & 0xFFFFFFFF
        return (~checksum) & 0xFF  # 取反并取低8位

    # 解析小包
    def parse_small_packet(self, packet):
        rawdata = (packet[5] << 8) | packet[6]
        if rawdata > 32768:
            rawdata -= 65536
        self.raw_data.append(rawdata)
        self.update_data_display("原始数据", str(rawdata))

    # 解析大包
    def parse_large_packet(self, packet):
        eeg_power_labels = list(self.eeg_powers.keys())
        for i, label in enumerate(eeg_power_labels):
            start_index = 7 + i * 3
            value = (packet[start_index] << 16) | (packet[start_index + 1] << 8) | packet[start_index + 2]
            self.eeg_powers[label].append(value)
            self.update_data_display(label, str(value))
        attention_value = packet[32]
        meditation_value = packet[34]
        self.attention.append(attention_value)
        self.meditation.append(meditation_value)
        
    #更新数据显示
    def update_data_display(self, data_type, value):
        if data_type in self.data_frames:
            self.data_frames[data_type].insert(tk.END, value + "\n")
            self.data_frames[data_type].see(tk.END)

    # 读取串口数据
    def read_serial_data(self):
        def read():
            while self.is_serial_open:
                if self.serial_port.in_waiting > 0:
                    new_data = self.serial_port.read(self.serial_port.in_waiting)
                    self.buffer.extend(new_data)
                    self.process_buffer()

        threading.Thread(target=read, daemon=True).start()

    def process_buffer(self):
        while len(self.buffer) >= 8:
            if self.buffer[0:2] == b'\xAA\xAA':
                if self.buffer[2] == 0x04 and len(self.buffer) >= 8:  # 小包
                    packet = self.buffer[:8]
                    self.buffer = self.buffer[8:]
                    self.parse_small_packet(packet)
                elif self.buffer[2] == 0x20 and len(self.buffer) >= 36:  # 大包
                    packet = self.buffer[:36]
                    self.buffer = self.buffer[36:]
                    self.parse_large_packet(packet)
                else:
                    self.buffer = self.buffer[1:]
            else:
                self.buffer = self.buffer[1:]

    # 更新图表
    def update_plots(self):
        if self.plot_enabled.get():
            current_time = time.time() * 1000

            if current_time - self.last_raw_eeg_update >= self.raw_eeg_update_interval:
                self.update_raw_eeg_plot()
                self.last_raw_eeg_update = current_time

            if current_time - self.last_other_charts_update >= self.other_charts_update_interval:
                self.update_other_charts()
                self.last_other_charts_update = current_time

        self.root.after(10, self.update_plots)

    def update_raw_eeg_plot(self):
        self.raw_line.set_data(range(len(self.raw_data)), self.raw_data)
        self.axs[0].relim()
        self.axs[0].autoscale_view()
        self.canvas.draw_idle()

    def update_other_charts(self):
        for i, power in enumerate(self.eeg_powers.values()):
            if power:
                self.power_bars[i].set_height(power[-1])

        x = range(len(self.attention))
        self.attention_line.set_data(x, self.attention)
        self.meditation_line.set_data(x, self.meditation)
        self.axs[2].relim()
        self.axs[2].autoscale_view()

        self.canvas.draw_idle()

    #导出数据
    def export_data(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                headers = ["Raw Data"] + list(self.eeg_powers.keys())
                writer.writerow(headers)

                max_length = max(len(self.raw_data), max(len(power) for power in self.eeg_powers.values()))
                
                for i in range(max_length):
                    row = []
                    row.append(self.raw_data[i] if i < len(self.raw_data) else '')
                    for power in self.eeg_powers.values():
                        row.append(power[i] if i < len(power) else '')
                    writer.writerow(row)

            messagebox.showinfo("导出成功", f"数据已保存到 {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialApp(root)
    root.mainloop()