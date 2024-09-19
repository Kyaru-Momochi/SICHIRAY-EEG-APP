import tkinter as tk
from tkinter import filedialog, messagebox
import serial
import threading

class SerialApp:
    def __init__(self, root):
        self.root = root
        self.root.title("串口数据接收器")
        self.serial_port = None
        self.baud_rate = 9600
        self.is_serial_open = False

        # 左侧数据输出框
        self.text_output = tk.Text(self.root, height=20, width=60)
        self.text_output.grid(row=0, column=0, padx=10, pady=10)

        # 右侧功能按钮
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=0, column=1, padx=10, pady=10)

        # 打开串口按钮
        self.open_button = tk.Button(button_frame, text="打开串口", command=self.open_serial)
        self.open_button.grid(row=0, column=0, pady=5)

        # 关闭串口按钮
        self.close_button = tk.Button(button_frame, text="关闭串口", command=self.close_serial, state=tk.DISABLED)
        self.close_button.grid(row=1, column=0, pady=5)

        # 设置波特率输入框和按钮
        tk.Label(button_frame, text="波特率:").grid(row=2, column=0)
        self.baud_entry = tk.Entry(button_frame)
        self.baud_entry.insert(0, "9600")  # 默认波特率
        self.baud_entry.grid(row=3, column=0, pady=5)

        self.set_baud_button = tk.Button(button_frame, text="设置波特率", command=self.set_baud_rate)
        self.set_baud_button.grid(row=4, column=0, pady=5)

        # 清空窗口按钮
        self.clear_button = tk.Button(button_frame, text="清空窗口", command=self.clear_output)
        self.clear_button.grid(row=5, column=0, pady=5)

        # 保存窗口内容到文件按钮
        self.save_button = tk.Button(button_frame, text="保存到文件", command=self.save_to_file)
        self.save_button.grid(row=6, column=0, pady=5)

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

    # 读取串口数据
    def read_serial_data(self):
        def read():
            while self.is_serial_open:
                if self.serial_port.in_waiting > 0:
                    try:
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        hex_data = data.hex().upper()  # 转换为十六进制
                        self.text_output.insert(tk.END, f"接收到的数据: {hex_data}\n")
                        self.text_output.see(tk.END)  # 自动滚动到底部
                    except serial.SerialException as e:
                        self.text_output.insert(tk.END, f"读取错误: {e}\n")
                        self.is_serial_open = False
                        break
        threading.Thread(target=read, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = SerialApp(root)
    root.mainloop()
