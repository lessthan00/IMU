# 介绍

这可以将gerber2格式的 gerber 文件, 无论是带文件后缀的,还是文件后缀统一命名的.
可以统一转换为jlc 的pcb 免费打板认可的gerber文件

## 使用

1. kicad的gerber 文件仿真 kicad_gerber 的文件夹下

```txt
project
--kicad_gerber
----...kicad的gerber文件
--kicad_ad2jlc_gerber.exe
```

双击 kicad_ad2jlc_gerber.exe
生成

```txt
project
--kicad_gerber
----...kicad的gerber文件
--jlc_gerber
----...jlc的gerber文件
--kicad_ad2jlc_gerber.exe
--jlc_gerber.zip
```

然后jlc_gerber.zip 即可拿去免费打板

2. AD的Gerber

```txt
project
--ad_gerber
----...ad的gerber文件
--kicad_ad2jlc_gerber.exe\
```

双击 kicad_ad2jlc_gerber.exe
生成

```txt
project
--ad_gerber
----...ad的gerber文件
--jlc_gerber
----...jlc的gerber文件
--kicad_ad2jlc_gerber.exe
--jlc_gerber.zip
```

然后jlc_gerber.zip 即可拿去免费打板

## 原理

gerber2 的内容已经规定好了,jlc并不能更改,所以识别是否为jlc 的eda产生的gerber,实际上用的
gerber的命名,gerber文件的文件头(作为注释),gerber的zip的命名

假如你上传两个gerber.zip,内容不一样,但命名一样,你会得到一样的打板,就是先打板下单的那一个为准.

所以只需要对应好,添加文件头注释,修改文件命名,修改gerber.zip的命名即可.

## 制作exe

python 环境安装
cd kicad_ad2jlc_gerber_python
./make.ps1

如果报错,就把 make.ps1的内容复制到 powershell的命令行来运行即可
即可获得 exe文件

## make.ps1
pip install pyinstaller

# 清理之前的编译
Remove-Item dist, build, jlc_gerber -Recurse -ErrorAction Ignore

# 执行编译
pyinstaller --onefile --name "2jlc" --add-data "GerberX2.json" --hidden-import=shutil --hidden-import=csv 2jlc.py


## change

# 会改变的地址,在exe外部, 这个文件的目录
self_PATH = get_exe_dir()

BASE_PATH = os.path.dirname(os.path.dirname(self_PATH))

# 构建路径
PATH_FINAL = os.path.join(BASE_PATH, r'output/jlc_gerber')
gerber_folder = os.path.join(BASE_PATH, r"output/gerber")
timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
zip_path = os.path.join(BASE_PATH, f"output/out_{get_gerber_file_prefix(gerber_folder)}-{timestamp}.zip")