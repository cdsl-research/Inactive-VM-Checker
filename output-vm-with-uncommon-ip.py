#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shutil
from glob import glob

#---------------------------------------------------------
# 前処理
#
# vm-status配下にある "X-last-tcpdump.txt" に対応する "X" ディレクトリのファイルを削除し、
# "X-last-tcpdump.txt" を "X" にリネームして整理する。
#
# その後、4項目（TIMESTAMP, KUBE, LAST, TCPDUMP）に分解して vm-status/tmp 下に
# {VM名}-TIMESTAMP.tmp, {VM名}-KUBE.tmp, {VM名}-LAST.tmp, {VM名}-TCPDUMP.tmp を作成する。
#
# また、{VM名}-LAST.tmp から "reboot" と "Nov  6" を含む行を削除する。
#---------------------------------------------------------

vm_status_dir = "vm-status"
tmp_dir = os.path.join(vm_status_dir, "tmp")
data_dir = "data"

os.makedirs(tmp_dir, exist_ok=True)
os.makedirs(os.path.join(data_dir), exist_ok=True)

# 1. "X-last-tcpdump.txt" を探して処理
last_tcpdump_files = glob(os.path.join(vm_status_dir, "*-last-tcpdump.txt"))
for last_tcpdump_file in last_tcpdump_files:
    # VM名を抽出 (例: vm-status/c0a22099-vm03-last-tcpdump.txt -> c0a22099-vm03)
    basename = os.path.basename(last_tcpdump_file)
    vm_name = basename.replace("-last-tcpdump.txt","")
    vm_dir = os.path.join(vm_status_dir, vm_name)

    # vm-status/X のファイルをすべて削除(ディレクトリなら中身を削除)
    if os.path.exists(vm_dir):
        # ディレクトリの場合は中を空に
        if os.path.isdir(vm_dir):
            for f in glob(os.path.join(vm_dir, "*")):
                if os.path.isfile(f):
                    os.remove(f)
                else:
                    shutil.rmtree(f)
        else:
            # ファイルなら削除
            os.remove(vm_dir)
        # vm-status/X自体は削除しない(ディレクトリの場合は空のまま残る)
    else:
        # vm_dirが存在しない場合、新規で作る
        os.makedirs(vm_dir, exist_ok=True)

    # "-last-tcpdump.txt"を"X"にリネーム (ここでXはファイル名ではなく、vm-status/Xディレクトリ内ファイルとして保存)
    # 要件から読み取れる限り、X-last-tcpdump.txtはVM情報ファイルとなるので、vm-status/Xに格納
    dst_file = os.path.join(vm_dir, vm_name)  # vm-status/X/X というファイル名で格納
    if os.path.exists(dst_file):
        os.remove(dst_file)
    shutil.move(last_tcpdump_file, dst_file)

    # dst_file を読み込み、4項目に分割
    # 項目は「TIMESTAMP, 空行, KUBE, 空行, LAST, 空行, TCPDUMP」という構造を想定
    # 空行でsplitする
    with open(dst_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # 空行でsplit
    sections = [sec.strip("\n") for sec in content.split("\n\n")]

    # sectionsは[Timestamp, Kube, LAST, TCPDUMP]の4つが想定
    if len(sections) != 4:
        # データ形式が期待と違う場合はログなど出力してスキップする
        # ここでは単純にcontinue
        continue

    timestamp_section = sections[0]
    kube_section = sections[1]
    last_section = sections[2]
    tcpdump_section = sections[3]

    # tmpファイル作成
    timestamp_tmp = os.path.join(tmp_dir, f"{vm_name}-TIMESTAMP.tmp")
    kube_tmp = os.path.join(tmp_dir, f"{vm_name}-KUBE.tmp")
    last_tmp = os.path.join(tmp_dir, f"{vm_name}-LAST.tmp")
    tcpdump_tmp = os.path.join(tmp_dir, f"{vm_name}-TCPDUMP.tmp")

    with open(timestamp_tmp, "w", encoding="utf-8") as f:
        f.write(timestamp_section + "\n")
    with open(kube_tmp, "w", encoding="utf-8") as f:
        f.write(kube_section + "\n")

    # LASTからrebootと"Nov  6"を含む行を削除
    filtered_last_lines = []
    for line in last_section.splitlines():
        if "reboot" in line or "Nov  6" in line:
            continue
        filtered_last_lines.append(line)
    with open(last_tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(filtered_last_lines) + "\n")

    with open(tcpdump_tmp, "w", encoding="utf-8") as f:
        f.write(tcpdump_section + "\n")


#---------------------------------------------------------
# 2. {VM名}-TCPDUMP.tmp ファイルに対する処理
#   ・2,3行目を削除
#   ・ARPを含む行を削除
#   ・1行中に存在する2つのIPアドレスを抽出し、改行で分割出力
#---------------------------------------------------------

tcpdump_tmps = glob(os.path.join(tmp_dir, "*-TCPDUMP.tmp"))
ip_pattern = re.compile(r"(\d+\.\d+\.\d+\.\d+)")

for tfile in tcpdump_tmps:
    with open(tfile, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # 2,3行目削除(インデックス1,2)
    # 行数が3行以上ある前提で対処、それ以下の場合はスキップ
    if len(lines) > 2:
        del lines[1:3]

    # ARPを含む行を削除
    lines = [l for l in lines if "ARP" not in l]

    # 1行中に2つのIPがあれば抽出し改行で分割
    new_lines = []
    for l in lines:
        ips = ip_pattern.findall(l)
        # 2つ以上見つかった場合、最初の2つを抽出
        if len(ips) >= 2:
            # 2つ目のIPで改行する
            # 例: "IP1\nIP2\n"
            # 他の情報は削除して、IPのみ残すことを想定
            new_lines.append(ips[0] + "\n" + ips[1] + "\n")
        else:
            # IPが2つ見つからない場合は行を無視するか、
            # 又は1つしかなければ1つだけ出力するか等、要件明確でないがここではスキップ
            continue

    with open(tfile, "w", encoding="utf-8") as f:
        f.write("".join(new_lines))


#---------------------------------------------------------
# 3. 共通するIPアドレスを抽出し，data/common-ip に出力
#
# すべての {VM名}-TCPDUMP.tmp から取得したIPアドレスを抽出し、
# すべてのVMに共通して含まれているIPを求める。
#---------------------------------------------------------

vm_tcpdump_data = {}
all_ips_sets = []  # 各VM毎のIPセットを格納

for tfile in tcpdump_tmps:
    vm_name = os.path.basename(tfile).replace("-TCPDUMP.tmp","")
    with open(tfile, "r", encoding="utf-8") as f:
        ips = set([line.strip() for line in f if line.strip()])
    vm_tcpdump_data[vm_name] = ips
    all_ips_sets.append(ips)

# 共通IP: 全てのVMが持つIPの積集合
if all_ips_sets:
    common_ips = set.intersection(*all_ips_sets)
else:
    common_ips = set()

common_ip_file = os.path.join(data_dir, "common-ip")
with open(common_ip_file, "w", encoding="utf-8") as f:
    for ip in sorted(common_ips):
        f.write(ip + "\n")


#---------------------------------------------------------
# 4. common-ip のみがあるVMを data/vm-with-common-ip に出力
#   ※ common_ipにあるIPのみ保持: VMが持つIPがすべてcommon_ipsに含まれる => vm-with-common-ipに書く
#---------------------------------------------------------

vm_with_common_ip_file = os.path.join(data_dir, "vm-with-common-ip")
with open(vm_with_common_ip_file, "w", encoding="utf-8") as f:
    for vm_name, ips in vm_tcpdump_data.items():
        if ips and common_ips and ips.issubset(common_ips):
            f.write(vm_name + "\n")


#---------------------------------------------------------
# 5. common-ip に記載されたIP以外があるVMを data/vm-with-uncommon-ip に出力
#   VMが持つIP集合の中にcommon_ips以外のIPが1つでもあれば対象
#---------------------------------------------------------

vm_with_uncommon_ip_file = os.path.join(data_dir, "vm-with-uncommon-ip")
with open(vm_with_uncommon_ip_file, "w", encoding="utf-8") as f:
    for vm_name, ips in vm_tcpdump_data.items():
        # ipsの中にcommon_ips以外があるか
        if not ips.issubset(common_ips):
            f.write(vm_name + "\n")
