#!/usr/bin/env python3

import os
import sys
import tty
import termios


DEBUG = 0
NOT_TEST_MODE = 1

def getch_linux():
    # Speichert die aktuellen Terminaleinstellungen
    fd = sys.stdin.fileno() # File Descriptor für Standard-Input
    old_settings = termios.tcgetattr(fd)
    try:
        # Schaltet das Terminal in den Raw-Modus
        # Zeichen werden sofort gelesen, kein Echo, keine Pufferung
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1) # Liest ein einzelnes Zeichen
    finally:
        # Stellt die ursprünglichen Terminaleinstellungen wieder her
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def get_drives() -> list[list[str]]:
    dev = os.popen("lsblk").read().strip("\n")
    dev_list = dev.split("\n")[1:]
    dev_list_item = []
    for i in dev_list:
        ii = i.split(" ")
        tmp = []
        for j in ii:
            if j == "":
                continue
            tmp.append(j.strip("├─").strip("└─"))
        if len(tmp) == 6:
            dev_list_item.append([tmp[0], tmp[3], tmp[5]])
        else:
            dev_list_item.append([tmp[0], tmp[3], tmp[5], tmp[6]])
        
    return dev_list_item

def get_mount_points() -> list[str]:
    mount_points = os.popen("ls /mnt/").read().strip("\n").split("\n")
    return mount_points


def get_max_len(data, row):
    max_len = 0
    for i in data:
        if len(i[row]) > max_len:
               max_len = len(i[row])
    # print(max_len)
    return max_len + 2


def print_to_ter(dev, select):
    pading = [0, 0, 0, 8]
    for n, i in enumerate(pading[:3]):
        pading[n] = get_max_len(dev, n)


    for n, i in enumerate(dev):
        string = ""
        offset = 0
        if n == select:
            string += "\033[47m"
            string += "\033[30m"
        if i[2] == "part":
            string += "  "
            offset = -2
        else:
            # hiligth disk's
            string += "\033[0;36m"


        string += f"{i[0]:<{pading[0] + offset}}  {i[1]:>{pading[1]}}  {i[2]:<{pading[2]}}" 
        if len(i) == 4:
            string += f"{i[3]:<{pading[3]}}"
        else:
            string += f"{'':<{pading[3]}}"

        # reset text
        string += "\033[0m"


        print(string)


def print_to_ter_mountpoint(mnt, select, selectable):
    pading = [10]
    for n, i in enumerate(pading[:]):
        pading[n] = get_max_len(dev, n)


    for n, i in enumerate(mnt):
        string = ""
        offset = 0
        if n == select:
            string += "\033[47m"
            string += "\033[30m"

        if n not in selectable:
            string += "\033[0;31m"


        string += f"{i:<{pading[0] + offset}}" 

        # reset text
        string += "\033[0m"


        print(string)


def get_selectable(data):
    selectable = []
    for n, i in enumerate(data):
        if i[2] == "part":
            selectable.append(n)
    return selectable


def get_selectable_mount(dev, mnt):
    mountet = []
    selectable = []

    for i in dev:
        if len(i) >= 4:
            mountet.extend(i[3].split("/"))

    for n, i in enumerate(mnt):
        if i not in mountet:
            selectable.append(n)
    return selectable


def get_target_disk(dev):
    selectable = get_selectable(dev)
    select = 0
    select_max = len(selectable) - 1
    get_char = " "

    while True:
        if DEBUG:
            print(f"{select}/{select_max}")
            print(f"key = {get_char},\tsignal = {ord(get_char)}")
        print("move: j, k | Select : Enter | Exit: q")
        print_to_ter(dev, selectable[select])
        get_char = getch_linux()
        # geht nicht???
        # print("\033c", end="")
        # print("\033[2J", end="")
        os.system("clear")
        if get_char == "q":
            return 1
        if ord(get_char) == 3:  # CTRL + C
            return 1
        elif get_char == "j":
            if select >= select_max:
                select = 0
            else:
                select += 1
                
        elif get_char == "k":
            if select <= 0:
                select = select_max
            else:
                select -= 1
        elif ord(get_char) == 13:
            break

    
    return dev[selectable[select]]


def get_target_disk_mount(dev, mnt):
    selectable = get_selectable_mount(dev, mnt)
    # selectable = range(0, len(mnt))
    select = 0
    select_max = len(selectable) - 1
    get_char = " "

    while True:
        if DEBUG:
            print(f"{select}/{select_max}")
            print(f"key = {get_char},\tsignal = {ord(get_char)}")
        print("move: j, k | Select : Enter | Exit: q")
        print_to_ter_mountpoint(mnt, selectable[select], selectable)
        get_char = getch_linux()
        os.system("clear")
        if get_char == "q":
            return 1
        if ord(get_char) == 3:  # CTRL + C
            return 1
        elif get_char == "j":
            if select >= select_max:
                select = 0
            else:
                select += 1
                
        elif get_char == "k":
            if select <= 0:
                select = select_max
            else:
                select -= 1
        elif ord(get_char) == 13:
            break

    
    return mnt[selectable[select]]


def mount_usb(dev: str, mnt: str):
    if DEBUG:
        print(f"sudo mount -o uid=1000 /dev/{dev} /mnt/{mnt}")
    if NOT_TEST_MODE:
        prosses = os.system(f"sudo mount -o uid=1000 /dev/{dev} /mnt/{mnt}")
        if prosses == 0:
            print("USB-Sick ist einsatz bereit")


def umount_usb(mnt: str):
    if DEBUG:
        print(f"sudo umount /mnt/{mnt.removeprefix('/mnt/')}")
    if NOT_TEST_MODE:
        prosses = os.system(f"sudo umount /mnt/{mnt.removeprefix('/mnt/')}")
        if prosses == 0:
            print("Der USB-Sick kann nun entfert werden.")



if __name__ == "__main__":
    dev = get_drives()

    os.system("tput smcup")
    dev_target = get_target_disk(dev)
    # os.system("tput rmcup")
    if dev_target == 1:
        os.system("tput rmcup")
        exit(1)



    if len(dev_target) >= 4:
        os.system("tput rmcup")
        if dev_target[3].startswith("/mnt/"):
            umount_usb(dev_target[3])
            exit(0)
        else:
            print("Das Gerät ist schon gemoutet und kann/soll nicht entfert werden!")
            print(f'Falls du es doch entferene willst: "sudo umount {dev_target[3]}"')
            exit(1)

    mnt = get_mount_points()
    mnt_target = get_target_disk_mount(dev, mnt)
    if mnt_target == 1:
        os.system("tput rmcup")
        exit(1)
    os.system("tput rmcup")
    mount_usb(dev_target[0], mnt_target)


    # Print the size of terminal
    # columns, lines = os.get_terminal_size()
    # columns=125, lines=35

    # ├─
    # └─
