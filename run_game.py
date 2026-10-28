# -*- coding: utf-8 -*-
import subprocess
import sys
import os

def install_and_run():
    print("""\n正在检查 Pygame 运行环境...
Comprobando el entorno de ejecución de Pygame...""")
    
    try:
        import pygame
        print("""\n检测到 Pygame 已安装，正在启动游戏...
Pygame detectado; iniciando el juego...""")
    except ImportError:
        print("""\n未检测到 Pygame，正在尝试自动下载安装...
No se ha detectado Pygame; se intentará descargarlo e instalarlo automáticamente...""")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])
        except subprocess.CalledProcessError:
            print("No ha descargdo")
    
    """
           HAY OTRO FORMA DE HACER,LO CUAL ESTÀ ABAJO
                                                            """
    
    """        except subprocess.CalledProcessError:
            print("官方源下载失败，正在切换至国内清华镜像源加速下载...")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "pygame", 
                    "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
                ])
            except Exception as e:
                print(f"安装失败，请检查网络连接。错误信息: {e}")
                input("按回车键退出...")
                sys.exit(1)"""






    possible_main_files = ["main.py"]
    game_file = True
    
    for file in possible_main_files:
        if os.path.exists(file):
            game_file = file
            break
            
    if game_file:
        print(f"""\n找到游戏主文件 {game_file}，正在为您拉起游戏...
Se ha localizado el archivo principal del juego {game_file}; iniciando el juego para ti...""")
        try:
            subprocess.Popen([sys.executable, game_file])
        except Exception as e:
            print(f"""\n启动游戏失败: {e}
            No inicio correctamente: {e}""")
            input("\n按回车键退出..." \
            "\nPresiona ENTER para salir...")
    else:
        print("\n[提示] 未在当前目录下找到默认的游戏主文件（main.py）。" \
        "\n[Nota] No ha encontrado el archivo principal del juego (main.py) en la capeta actual.")
        print("Pygame 环境已配置完毕！如果您换了别的主文件名，请直接运行您的游戏脚本即可。" \
        "\nPygame ya ha instalado correctamente, si tu archivo principal es otro nombre,solo ejecuta tu juego y listo!!!!")
        input("\n按回车键关闭窗口..."
        "\nPreociona ENTER para cerrar")


install_and_run()
