# SICHIRAY-EEG-APP

## 本项目旨在针对思知瑞脑波套件的数据读取和导出

![image-20240919145228558](https://github.com/user-attachments/assets/791bcd84-cdd9-43db-bd89-b7db0dddd6a2)


本套件含有以下部分：蓝牙适配器x1、硅胶头带&发送器x1、充电线x1

![image-20240919145203476](https://github.com/user-attachments/assets/4b0ba302-9127-492e-8ec2-ab67c35a9c91)


## 如何使用

### 1、安装CH340/CH341驱动

下载地址：(https://www.wch.cn/download/CH341SER_EXE.html)

### 2、将蓝牙适配器插入任意USB端口

右键“此电脑”/“我的电脑”-->点击管理-->在左侧点击设备管理器-->打开端口（COM和LPT）-->找到蓝牙适配器对应的USB串行设备，如图

![image-20240920123346494](https://github.com/user-attachments/assets/063e28ed-361c-44e9-8d2f-1f635e5f0f55)

记住端口号（我这里是COM12），若实在不知道，先拔掉适配器，再插上，看看新增的端口号是哪个

### 3、戴上头带

戴上头带，发送器应在额头左侧，夹子夹住左耳垂（额头电极部位与耳垂需先沾水以维持导电性），打开发送器上的开关，听见“滴”一声，适配器蓝灯常亮即连接成功

### 4、打开软件

选择端口：在此处选择刚刚设备管理器中显示的蓝牙适配器所对应的端口号（如COM12）

波特率：默认为9600，不需要修改

启用绘图：默认开启，因绘图性能开销较大，专注数据采集时不建议开启

选择串口后点击打开串口，开始接收数据

数据导出：点击左上角文件，选择导出数据，即可保存为CSV文件

### 5、注意事项

不要随意更改窗口大小，过大的窗口会导致极其卡顿（绘图导致的，待解决）

#### 6、碎碎念

由于python性能问题后续看情况可以换成别的语言-_-
