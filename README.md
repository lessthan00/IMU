# IMU_ESP32S3_MPU6050_HMC5883L_SSD1306  
  
## 基于ESP32的IMU系统与OLED显示屏  
  
### 简介  
  
本项目实现了一个基于ESP32微控制器的惯性测量单元（IMU）系统，集成了MPU6050（6轴加速度计和陀螺仪）、HMC5883L（3轴磁力计）和SSD1306 OLED显示屏（128x64像素）。系统通过卡尔曼滤波融合传感器数据，实时计算并显示设备的俯仰（pitch）、滚转（roll）和偏航（yaw）角度，适用于机器人、无人机或可穿戴设备等需要精确姿态测量的场景。  
  
### 硬件要求  
  
#### 元件清单  
  
| 元件                     | 描述                                   | 备注                              |  
|--------------------------|----------------------------------------|-----------------------------------|  
| ESP32微控制器            | ESP32开发板（如DevKitC）或ESP32S3芯片 | ESP32S3需USB转串口烧录           |  
| MPU6050传感器模块        | 6轴加速度计和陀螺仪                   | I2C通信，地址0x68或0x69          |  
| HMC5883L传感器模块       | 3轴数字磁力计                         | I2C通信，地址0x1E                 |  
| SSD1306 OLED显示屏       | 128x64像素                            | I2C通信                           |  
| 触控按钮（4个）          | 用于电源、模式、冻结和预留功能         | 连接到GPIO 15、16、17、18         |  
| 跳线                     | 用于连接元件                           |                                   |  
| 面包板或PCB              | 用于安装元件                           |                                   |  
| 电源                     | 若不使用带USB的开发板需单独电源        | 3.3V                              |  
| USB转串口转换器          | 如CP2102或CH340，仅ESP32S3芯片需要     | 用于程序烧录                      |  
  
#### 引脚接线图  
  
所有传感器和显示屏通过I2C接口连接到ESP32的GPIO 21（SDA）和GPIO 22（SCL）。按钮连接到指定GPIO引脚。以下是详细接线表：  
  
| 元件         | 引脚 | ESP32连接 | 备注                     |  
|--------------|------|-----------|--------------------------|  
| MPU6050      | SDA  | GPIO 11   | I2C数据线                |  
| MPU6050      | SCL  | GPIO 12   | I2C时钟线                |  
| MPU6050      | VCC  | 3.3V      | 电源                     |  
| MPU6050      | GND  | GND       | 接地                     |  
| HMC5883L     | SDA  | GPIO 11   | I2C数据线                |  
| HMC5883L     | SCL  | GPIO 12   | I2C时钟线                |  
| HMC5883L     | VCC  | 3.3V      | 电源                     |  
| HMC5883L     | GND  | GND       | 接地                     |  
| SSD1306 OLED | SDA  | GPIO 11   | I2C数据线                |  
| SSD1306 OLED | SCL  | GPIO 12   | I2C时钟线                |  
| SSD1306 OLED | VCC  | 3.3V      | 电源                     |  
| SSD1306 OLED | GND  | GND       | 接地                     |  
| 电源按钮     | -    | GPIO 15   | 控制电源开关             |  
| 模式按钮     | -    | GPIO 16   | 切换绝对/相对模式        |  
| 冻结按钮     | -    | GPIO 17   | 冻结/解冻显示            |  
| 预留按钮     | -    | GPIO 18   | 预留未来功能             |  
  
**ESP32S3芯片额外接线**（若使用芯片而非开发板）：  
- TX（ESP32S3）→ RX（USB转串口）  
- RX（ESP32S3）→ TX（USB转串口）  
- CH_PD（ESP32S3）→ 3.3V（USB转串口）  
- EN（ESP32S3）→ 3.3V（USB转串口）  
- GND（ESP32S3）→ GND（USB转串口）  
- VCC（ESP32S3）→ 3.3V（USB转串口）  
  
**注意**：所有I2C设备（MPU6050、HMC5883L、SSD1306）共享相同的SDA和SCL线。按钮连接需使用内部上拉电阻或外部上拉电阻。  
  
### 软件结构  
  
#### 程序结构框图  
  
软件基于FreeRTOS实现多任务处理，包含以下并发任务：  
- **传感器任务**：以20 Hz频率从MPU6050和HMC5883L读取数据，发送到传感器队列。  
- **处理任务**：从传感器队列接收数据，使用卡尔曼滤波计算姿态（俯仰、滚转、偏航），以5 Hz频率发送到姿态队列。  
- **显示任务**：从姿态队列接收数据，以5 Hz频率更新OLED显示屏。  
- **按钮任务**：监控按钮状态，处理电源开关、模式切换（绝对/相对）和显示冻结。  
- **初始化与校准任务**：启动时初始化I2C接口、传感器，并执行校准。  
  
**框图描述**：  
- **输入**：MPU6050（加速度、角速度）、HMC5883L（磁场）  
- **任务流程**：  
  - 传感器任务 → 传感器队列 → 处理任务 → 姿态队列 → 显示任务  
  - 按钮任务 → 处理用户输入  
- **输出**：SSD1306 OLED显示屏  
- **同步机制**：使用FreeRTOS队列（`sensor_queue`、`attitude_queue`）和信号量（`i2c_mutex`、`ssd1306_mutex`、`calibration_done_sem`）进行任务间通信和资源保护。  
  
#### 流程图  
  
1. **启动**：  
   - 初始化ESP32S3外设（I2C、GPIO）  
   - 创建FreeRTOS任务和队列  
2. **校准**：  
   - 校准MPU6050（加速度计和陀螺仪，设备需静止）  
   - 校准HMC5883L（磁力计，需缓慢旋转设备）  
3. **主循环**：  
   - 传感器任务：持续读取传感器数据并发送到队列  
   - 处理任务：从队列接收数据，处理并发送到显示队列  
   - 显示任务：从队列接收数据，更新显示屏  
   - 按钮任务：持续监控按钮并处理事件  
4. **关机**：  
   - 长按电源按钮，暂停任务并关闭系统  
  
### 传感器与显示屏简介  
  
#### MPU6050  
  
MPU6050是一个6轴惯性测量单元，包含3轴加速度计（量程±4g）和3轴陀螺仪（量程±500 dps）。它通过I2C通信（地址0x68或0x69），用于测量设备的俯仰和滚转角度。更多信息可参考 [MPU6050教程](https://www.instructables.com/Connecting-MPU6050-With-ESP32/)。  
  
#### HMC5883L  
  
HMC5883L是一个3轴数字磁力计，用于测量磁场以确定偏航（罗盘方向）。它通过I2C通信（地址0x1E），支持倾斜补偿以提高精度。更多信息可参考 [HMC5883L与ESP32接口](https://circuitdigest.com/microcontroller-projects/diy-smartwatch-using-esp32-part3-interfacing-magnetometer-and-gyroscope-with-esp32)。  
  
#### SSD1306 OLED显示屏  
  
SSD1306是一个128x64像素的OLED显示屏，通过I2C通信，显示实时传感器数据，包括俯仰、滚转、偏航、加速度、陀螺仪和磁力计读数。支持绝对和相对模式，并可根据Z轴加速度自动翻转显示。更多信息可参考 [ESP32与SSD1306教程](https://randomnerdtutorials.com/esp32-ssd1306-oled-display-arduino-ide/)。  
  
### 使用说明  
  
#### 硬件设置  
  
1. 按照引脚接线图连接MPU6050、HMC5883L、SSD1306和按钮到ESP32S3。  
2. 若使用ESP32S3芯片，连接USB转串口模块（TX、RX、CH_PD、EN、GND）。  
3. 使用面包板或PCB固定元件，确保3.3V电源稳定。  
  
#### 程序烧录  
  
1. **使用ESP32S3开发板**：  
   - 通过USB连接开发板到计算机。  
   - 使用ESP-IDF或Arduino IDE（需安装ESP32支持）上传`main.c`程序。  
2. **使用ESP32S3芯片**：  
   - 连接USB转串口模块（如CP2102或CH340）。  
   - 使用ESP-IDF或Arduino IDE烧录程序，确保正确配置串口引脚。  
  
#### 操作  
  
- **开机**：短按电源按钮（GPIO 15）。  
- **关机**：长按电源按钮（>2秒）。  
- **模式切换**：按模式按钮（GPIO 16）切换绝对/相对测量模式。  
- **冻结显示**：按冻结按钮（GPIO 17）冻结/解冻显示。  
- **预留功能**：预留按钮（GPIO 18）为未来功能保留。  
  
### 调试与日志  
  
- 系统使用ESP_LOG框架记录日志，标签为“mpu6050 test”和“SSD1306”。  
- 定期记录任务堆栈使用情况以监控内存使用。  
- 校准期间需保持设备静止（MPU6050）或缓慢旋转（HMC5883L）。  
  
### 当前存在的问题  
  
1. **数据更新速度慢**：  
   - 传感器任务以20 Hz频率生成数据，而处理任务和显示任务以5 Hz频率消费数据，导致生产速度快于消费速度，可能造成`sensor_queue`和`attitude_queue`队列满溢。日志中会记录“传感器队列已满”或“姿态队列已满”的警告。  
   - **潜在解决方案**：优化处理任务的计算效率（如简化卡尔曼滤波算法）或增加队列大小，同时调整任务调度优先级以平衡生产和消费速度。  
  
2. **关机后无法正常开机**：  
   - 系统运行一段时间后，关机（长按电源按钮）并再次短按电源按钮可能无法正常开机，表现为任务未正确恢复或系统未完全初始化。  
   - **潜在原因**：可能是任务挂起/恢复逻辑问题，或电源管理状态未正确重置。需要检查`button_task`中的任务恢复逻辑和硬件电源管理电路。  
  
### 未来展望  
  
1. **添加可视化更好的仪表界面**：  
   - 当前SSD1306显示屏以文本形式显示数据，未来计划开发图形化仪表界面（如指针式仪表或3D姿态可视化），以提高用户体验。  
   - 实现方式可能包括使用SSD1306的图形库绘制动态仪表盘，或升级到更高分辨率的显示屏（如SSD1327或彩色TFT屏）以支持更复杂的可视化。  
   - 需优化显示任务以确保图形渲染不影响实时性能。  
  
## 硬件从新设计  
  
### 物料  
  
GY-521模块,MPU6050,接口定义VCC,GND,SCL,SDA,XDA,SCL,ADO,INT  
GY-271模块,HMC5883L,接口定义VCC,GND,SCL,SDA,DRDY  
轻触开关  
0.96寸OLED SSD1306模块,接口定义VCC,GND,SCL,SDA  
因为I2C总线的通讯拥挤,可以选择使用SPI通讯.  
0.96村OLED SSD1306模块,7针接口定义 GND,VCC,D0,D1,RES,DC,CS  
GND 电源地, VCC 3.3V~5V, D0, SPI时钟线(SPI_CLK), D1,SPI数据线(SPI_MOSI), RES,复位, DC, 数据/命令选择脚,CS,片选信号,低电平有效,CS不可悬空.  
CH340G  
ESP32-S3FN8  
ESP32-S3-WROOM-1-N16R8  
  
### [H/W 硬件参考](https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32s3/hw-reference/index.html)  
  
[技术参考手册 (PDF)](https://www.espressif.com/sites/default/files/documentation/esp32-s3_technical_reference_manual_cn.pdf)  
[技术规格书 (PDF)](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_cn.pdf)  
  
### SPI分配  
  
### [SPI2 管脚对应表](https://docs.espressif.com/projects/esp-idf/zh_CN/stable/esp32s3/api-reference/peripherals/spi_master.html#gpio-io-mux)  
  
| 管脚名称  | GPIO编号 (SPI2) |  
|----------|----------------|  
| CS0      | 10             |  
| SCLK     | 12             |  
| MISO     | 13             |  
| MOSI     | 11             |  
| QUADWP   | 14             |  
| QUADHD   | 9              |  
  
#### [技术规格书 (PDF)](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_cn.pdf)  
  
##### 第 30 章 SPI 控制器(SPI)  
  
##### 30.1 概述  
  
串行外设接口(SPI)是一种同步串行接口，可用于与外围设备进行通信。ESP32-S3芯片集成了四个SPI控制  
器：  
• SPI0  
 • SPI1  
 • 通用SPI2，即GP-SPI2  
 • 和通用SPI3，即GP-SPI3  
 SPI0 和 SPI1 控制器主要供内部使用以访问外部flash及PSRAM。本章节主要介绍GP-SPI控制器，即GP-SPI2  
和GP-SPI3。  
  
(所以毫无疑问应该选择SPI2)  
  
##### 30.5.8.3 主机全双工通信（仅支持1-bit模式）  
  
| Master (GP-SPI2) | Direction | Slave  |  
|------------------|-----------|--------|  
| FSPID            | →         | MOSI   |  
| FSPIQ            | ←         | MISO   |  
| FSPICLK          | →         | CLK    |  
| FSPICS0          | →         | CS     |  
  
##### 附录A–ESP32-S3管脚总览  
  
GPIO9 ~ GPIO14 并未高亮,说明无限制和关键作用,可以放心使用.  
  
### I2C 分配  
  
[技术规格书 (PDF)](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_cn.pdf)  
  
#### 4.2.1.2 I2C 接口  
  
管脚分配  
I2C 的管脚可以为任意GPIO，通过GPIO交换矩阵配置。  
  
#### 2.3.1 IO MUX 功能  
  
部分直接源自特定外设（U0TXD、MTCK等），包括UART0/1、JTAG、SPI0/1和SPI2  
  
(意味着I2C 并没有不通过IO MUX 矩阵的更特殊接口)  
  
RTC_GPIO0,RTC_GPIO3均被标记为黄色  
  
#### [技术参考手册 (PDF)](https://www.espressif.com/sites/default/files/documentation/esp32-s3_technical_reference_manual_cn.pdf)2.3.4 GPIO 和RTC_GPIO 的限制  
  
本章节的表格中，部分管脚功能有高亮标记。推荐优先使用没有高亮的GPIO或RTC_GPIO管脚。  
如需更多管脚，请谨慎选择高亮的GPIO或RTC_GPIO管脚，避免与重要功能冲突。  
  
#### [技术规格书 (PDF)](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_cn.pdf)附录A–ESP32-S3管脚总览  
  
可知标黄原因:  
GPIO0,复位时IE,WPU,复位后IE,WPU.  
GPIO3,复位时IE,复位后IE.  
  
#### Boot 模式控制  
  
复位释放后，GPIO0、GPIO1、GPIO2和GPIO46在复位时的值将共同决定Boot模式。表8.2-1列出了GPIO0、  
GPIO1、GPIO2 和 GPIO46 的 Strapping 值及其对应的系统启动模式。  
表8.2-1. 系统启动模式  
  
| Boot Mode               | GPIO0 | GPIO46 | GPIO1 | GPIO2 |  
|-------------------------|-------|--------|-------|-------|  
| SPI Boot Mode           | 1     | x      | x     | x     |  
| Joint Download Boot Mode| 0     | 0      | x     | x     |  
| SPI Download Boot Mode  | 0     | 1      | 1     | 0     |  
  
x：任何取值均不会对结果有影响，因此可忽略。  
Joint Download Boot 模式下支持以下下载方式：  
• USB Download Boot  
   –USB-Serial-JTAG Download Boot  
   –USB-OTG Download Boot  
• UART Download Boot  
SPI DownloadBoot模式：GPIO1和GPIO2不是strapping管脚，但使用SPI Download Boot 模式时需要预留GPIO1和GPIO2。GPIO1和GPIO2默认浮空，在复位时处于高阻抗状态。  
  
在SPI Boot 模式下，ROM引导加载程序通过从SPIflash中读取程序来启动系统。SPIBoot模式可进一步细分为以下两种启动方式：  
• 常规flash启动方式：支持安全启动。ROM引导加载程序将程序从flash加载到SRAM，并执行。在大多数实际应用场景中，上述执行的程序多为二级引导程序，该二级引导程序将启动最终的应用程序。  
• 直接启动方式：不支持安全启动，程序直接从flash中运行。如需使能这一启动方式，请确保下载至flash的bin 文件其前两个字（地址：0x42000000）为0xaedb041d。  
在Joint Download Boot 模式下，用户可通过UART或USB接口将二进制文件下载至flash，或将二进制文件下载至SRAM并在SRAM中运行程序。  
在SPI Download Boot 模式下，用户可通过SPI接口将二进制文件下载至flash，或将二进制文件下载至SRAM并运行SRAM中的程序.  
  
所以GPIO0 GPIO1 GPIO2 GPIO3都最好不使用.  
  
#### 管脚配置一栏为复位时和复位后预设配置缩写  
  
•IE–输入使能  
•WPU–内部弱上拉电阻使能  
•WPD–内部弱下拉电阻使能  
• USB_PU–USB上拉电阻使能–USB管脚（GPIO19和GPIO20）默认开启USB功能，此时管脚是否上拉由USB上拉决定。USB上拉由USB_SERIAL_JTAG_DP/  
 DM_PULLUP控制，USB上拉电阻的具体阻值可通过USB_SERIAL_JTAG_PULLUP_VALUE位控制，详见《ESP32-S3技术参考手册》  
>章节USB串口/JTAG控制器。–USB管脚关闭USB功能时，用作普通GPIO，默认禁用管脚内部弱上/下拉电阻，可通过IO_MUX_FUN_WPU/WPD配置，  
详见《ESP32-S3技术参考手册》>章节IOMUX和GPIO交换矩阵。  
EFUSE_DIS_PAD_JTAG的值为  
• 0-弱上拉电阻使能  
• 1-管脚浮空  
  
### SSD1306 7PIN design  
  
[taobao](https://pan.baidu.com/s/1WhZjZDjIXnzRosZPsYRTPA?pwd=6666 )  
  
0.96村OLED SSD1306模块,7针接口定义 GND,VCC,D0,D1,RES,DC,CS  
  
| 引脚名称  | 描述                          | 备注                 |  
|----------|-----------------------------|---------------------|  
| GND      | 电源地                       |                     |  
| VCC      | 电源 (3.3V~5V)               | 工作电压范围         |  
| D0       | SPI时钟线 (SPI_CLK)          |                     |  
| D1       | SPI数据线 (SPI_MOSI)         |                     |  
| RES      | 复位信号                     |                     |  
| DC       | 数据/命令选择脚               |                     |  
| CS       | 片选信号 (低电平有效)         | 不可悬空             |  
  
### MPU6050 design  
  
copy from  [MPU6050](https://github.com/lessthan00/MPU6050)  
  
[JLC 页面](https://www.jlc-smt.com/lcsc/detail?componentCode=C24112)  
  
再次对比原理图封装无问题.  
对比芯片封装也无问题, 引脚间距0.5, QFN4x4mm, 热焊盘2.7x2.7, 打大过孔, 拉长焊盘,好焊接.  
  
[data sheet](https://item.szlcsc.com/datasheet/MPU-6050/24852.html)  
  
#### 描述  
  
其数字运动处理器(DMP)提供的融合运动数据输出，大幅降低了对系统处理器频繁轮询传感器数据的需求。  
1024字节片上FIFO缓冲区通过让系统处理器突发读取传感器数据后进入低功耗模式，有效降低系统整体功耗。  
封装 4x4x0.9mm(QFN)  
MPU-6050仅支持I2C串行接口且设有独立VLOGIC引脚；  
3轴陀螺仪、3轴加速度计及数字运动处理器™(DMP)。通过专用I2C传感器总线，可直接接入外部3轴电子罗盘数据，输出完整的9轴MotionFusion™融合数据。  
  
#### 7.2 Typical Operating Circuit  
  
对比电路图无问题,对比封装,无问题.  
  
I2C 上拉电阻10K  
AD0 下拉到地, 简化电路, 固定I2C 地址.  
FSYNC 帧同步数字输入,不使用下拉到地.  
CLKIN 外部输入时钟信号,不使用下拉到地.  
INT 需要找一个引脚.  
  
#### 9.2 I2C Interface  
  
当MPU-60X0与系统处理器通信时，始终作为从机设备工作（此时系统处理器担任主机角色）。SDA和SCL线路通常需要上拉电阻连接至VDD电源，总线最高传输速率为400kHz。  
  
MPU-60X0的7位从机地址为b110100X，其中最低位（LSB）由AD0引脚的电平状态决定。这一特性支持将两个MPU-60X0设备连接到同一I2C总线：在此配置下，一个设备的地址应为b1101000（AD0引脚置为逻辑低电平），另一个设备的地址则为b1101001（AD0引脚置为逻辑高电平）。  
  
所以I2C地址为 b1101000 (0x68) (104)  
  
#### DMP  
  
MPU-60X0系列芯片内置的数字运动处理器（DMP）可将运动处理算法的计算任务从主处理器卸载。该DMP能够从加速度计、陀螺仪及磁力计等第三方传感器获取数据并进行处理，处理结果既可通过DMP寄存器读取，也可存入FIFO缓冲区。DMP还可调用MPU的一个外部引脚来生成中断信号。  
  
DMP的核心价值在于为主处理器减轻时序处理负担并降低运算负荷。通常情况下，运动处理算法需以约200Hz的高频率运行才能保证低延迟的精确运算——即便应用层更新速率低至5Hz（如低功耗用户界面场景）也不例外。采用DMP可有效实现四大优势：降低系统功耗、简化时序控制、优化软件架构，并为应用程序节省宝贵的主处理器运算资源。  
  
(进一步了解发现好像DMP也没那么好用)  
  
### HMC5883L design  
  
[嘉立创 开发板模块资料](https://wiki.lckfb.com/zh-hans/esp32s3r8n8/module/sensor/hmc5883l-sensor.html)  
[采购链接](https://detail.tmall.com/item.htm?abbucket=15&id=615355218813&ns=1)  
[HMC5883L资料下载链接](https://pan.baidu.com/s/1DfYH5OQHmD8zj1fMbI6ffg) 提取码：8888  
[数据手册](https://cdn-shop.adafruit.com/datasheets/HMC5883L_3-Axis_Digital_Compass_IC.pdf)  
  
#### HMC5883L description  
  
sch copy from [QMC5883L](https://github.com/lessthan00/QMC5883L)  
  
霍尼韦尔 HMC5883L 是一种表面贴装的高集成模块，并带有数字接口的弱磁传感器芯片，应用于低成本罗盘和磁场检测领域。HMC5883L 包括最先进的高分辨率 HMC118X 系列磁阻传感器，并附带霍尼韦尔专利的集成电路包括放大器、自动消磁驱动器、偏差校准、能使罗盘精度控制在 1°~2°的 12 位模数转换器.简易的 I2C 系列总线接口。HMC5883L 是采用无铅表面封装技术，带有16引脚，尺寸为3.0X3.0X0.9mm。  
低电压工作(2.16-3.6V)和超低功耗（100uA）  
最大输出频率可达160Hz  
  
#### 供电压选择  
  
如果选择1.8V 供电, 会导致IO口需要转电平  
3.3V 供电是可行的,所以选择3.3V供电.  
  
#### I2C 地址转换表  
  
| 地址类型       | 十六进制格式 | 二进制格式    | 十进制格式 |  
|----------------|--------------|---------------|------------|  
| 7位设备地址    | 0x1E         | `b001 1110`    | 30         |  
| 8位读取地址    | 0x3D         | `b0011 1101`   | 61         |  
| 8位写入地址    | 0x3C         | `b0011 1100`   | 60         |  
  
##### 7位地址 → 8位地地址  
  
- 7位地址直接使用低7位  
- 8位地址在7位地址前补0，并在末尾添加R/W位：  
- **写入地址** = (7位地址 << 1) | 0  
   `0x1E << 1` = 0x3C  
   `0x3C | 0` = 0x3C  
- **读取地址** = (7位地址 << 1) | 1  
   `0x1E << 1` = 0x3C  
   `0x3C | 1` = 0x3D  
  
#### 引脚配置  
  
| 引脚编号 | 引脚名称 | 描述                                                                 |  
|----------|----------|----------------------------------------------------------------------|  
| 1        | SCL      | 串行时钟 - I2C总线主/从时钟                                          |  
| 2        | VDD      | 电源（2.16V-3.6V）                                                   |  
| 3        | NC       | 无连接                                                               |  
| 4        | S1       | 连接 VDDIO                                                           |  
| 5        | NC       | 无连接                                                               |  
| 6        | NC       | 无连接                                                               |  
| 7        | NC       | 无连接                                                               |  
| 8        | SETP     | 置位/复位带正-S/R电容（C2）连接                                      |  
| 9        | GND      | 电源接地                                                             |  
| 10       | C1       | 存储电容器（C1）连接                                                 |  
| 11       | GND      | 电源接地                                                             |  
| 12       | SETC     | S/R电容器（C2）连接-驱动端                                           |  
| 13       | VDDIO    | IO电源供应（1.7V-VDD）                                               |  
| 14       | NC       | 无连接                                                               |  
| 15       | DRDY     | 数据准备，中断引脚。内部被拉高。当数据位于输出寄存器时会在低电位上停250μsec |  
| 16       | SDA      | 串行数据 - I2C总线主/从数据                                          |  
  
### 按照推荐电路图设计  
  
I2C上拉电阻选择为10K  
  
### QMC5883L design  
  
这是HMC5883L的替代,引脚配置是一样的,封装也是一样的 LGA-16(3x3),轴的方向也一样,外围电路图也是一样.  
  
[QMC5883L JLC](https://www.jlc-smt.com/lcsc/detail?componentCode=C976032&spm=smt-pc.search-result.list.1)  
  
#### QMC5883L description  
  
QMC5883L 是一款多芯片三轴磁传感器。这款表面贴装、小尺寸芯片集成了磁传感器与信号调理专用集成电路（ASIC），主要面向无人机、机器人、移动设备及手持装置等高精度应用场景，如电子罗盘、导航和游戏交互。  
  
基于霍尼韦尔（Honeywell）授权的先进磁阻（AMR）技术，QMC5883L结合定制设计的16位模数转换器（ADC）ASIC，具有低噪声、高精度、低功耗、偏移消除和温度补偿等优势，可实现1°至2°的罗盘航向精度。其I²C串行总线接口便于快速集成。  
  
该传感器采用3x3x0.9mm³的16引脚栅格阵列（LGA）表面贴装封装。  
  
低电压工作(2.16-3.6V)和超低功耗（75uA）  
最大输出频率可达200Hz  

## 打板需要注意板厚

### RF要求50Ω共面单端阻抗

2层板 板厚1.6 铜厚1OZ  
线宽 19.8110mil 覆铜间距5mil  