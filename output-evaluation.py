#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
VM_STATUS_DIR = os.path.join(BASE_DIR, "vm-status")
TMP_DIR = os.path.join(VM_STATUS_DIR, "tmp")

INACTIVE_ANSWER_FILE = os.path.join(DATA_DIR, "answer", "inactive-vm")
ACTIVE_ANSWER_FILE = os.path.join(DATA_DIR, "answer", "active-vm")
PARTICIPATING_VM_FILE = os.path.join(DATA_DIR, "participating-vm.tmp")
ALL_ANSWER_INACTIVE_PARTICIPATING = os.path.join(DATA_DIR, "all-answer-inactive-of-participating-vm.tmp")
ALL_ANSWER_ACTIVE_PARTICIPATING = os.path.join(DATA_DIR, "all-answer-active-of-participating-vm.tmp")

INACTIVE_VM_PREDICTION_FILE = os.path.join(DATA_DIR, "inactive-vm-prediction")

# 実行時オプションで--clean-tmpが指定された場合はtmpファイル削除
clean_tmp = "--clean-tmp" in sys.argv
if clean_tmp:
    for f in glob.glob(os.path.join(TMP_DIR, "*.tmp")):
        os.remove(f)

# ---------------------------------------------------
# 1. vm-status/tmp から "-last-tcpdump"がつくファイル名を取得して
#    "-last-tcpdump"を取り除いてparticipating-vm.tmpに追加
#    そしてanswer/inactive-vm, answer/active-vmとのANDをとり
#    all-answer-inactive-of-participating-vm.tmp, all-answer-active-of-participating-vm.tmpを作成
# ---------------------------------------------------

# vm-status/tmp内で"-last-tcpdump"がつくファイル名を抽出
# ただし要件例にはtmp配下ではなくvm-status配下？要件再確認
# 「vm-status/tmpから「-last-tcpdump」が後ろにつくファイルの名前を...」とあるが、
# 実例から判断するとvm-status直下に置かれていたファイル。だが最終的ファイル構造では
# vm-status直下には{VM名}ファイルがあり、元々は{VM名}-last-tcpdump.txtがあった。
# ここでは一旦「vm-status/tmp」から"-last-tcpdump"がつくファイルを抽出することにする。
# もし異なるなら適宜修正。

last_tcpdump_files = glob.glob(os.path.join(VM_STATUS_DIR, "tmp", "*-last-tcpdump*"))
participating_vms = []
for fpath in last_tcpdump_files:
    fname = os.path.basename(fpath)
    vm = fname.replace("-last-tcpdump", "")
    participating_vms.append(vm)

# 重複除去
participating_vms = list(set(participating_vms))

with open(PARTICIPATING_VM_FILE, "w") as pf:
    for vm in sorted(participating_vms):
        pf.write(vm + "\n")

# ANDをとる関数
def read_lines(file):
    if not os.path.exists(file):
        return set()
    return set(l.strip() for l in open(file) if l.strip())

inactive_answer = read_lines(INACTIVE_ANSWER_FILE)
active_answer = read_lines(ACTIVE_ANSWER_FILE)
participating_set = set(participating_vms)

all_answer_inactive_participating = inactive_answer & participating_set
all_answer_active_participating = active_answer & participating_set

with open(ALL_ANSWER_INACTIVE_PARTICIPATING, "w") as w1:
    for vm in sorted(all_answer_inactive_participating):
        w1.write(vm + "\n")
with open(ALL_ANSWER_ACTIVE_PARTICIPATING, "w") as w2:
    for vm in sorted(all_answer_active_participating):
        w2.write(vm + "\n")

# ---------------------------------------------------
# 2. 推測結果との比較
#
# TP: 正解:inactive 且つ 推測:inactive
# TN: 正解:active 且つ 推測:active
# FP: 正解:active だが 推測:inactive
# FN: 正解:inactive だが 推測:active
#
# inactive-vm-prediction: 推測したinactive
# 参加VMからinactive-vm-predictionを除いた物が推測active
#
# 評価指標(適合率, 再現率, F値)
# 適合率 = TP / (TP+FP)
# 再現率 = TP / (TP+FN)
# F値 = 2*(適合率*再現率)/(適合率+再現率)
# ---------------------------------------------------

pred_inactive = read_lines(INACTIVE_VM_PREDICTION_FILE)
pred_active = participating_set - pred_inactive

true_inactive = all_answer_inactive_participating
true_active = all_answer_active_participating

TP = len(true_inactive & pred_inactive)  # 正解inactive & 推測inactive
TN = len(true_active & pred_active)      # 正解active & 推測active
FP = len(true_active & pred_inactive)    # 正解activeだが推測inactive
FN = len(true_inactive & pred_active)    # 正解inactiveだが推測active

precision = TP/(TP+FP) if (TP+FP) > 0 else 0.0
recall = TP/(TP+FN) if (TP+FN) > 0 else 0.0
f_value = (2*precision*recall)/(precision+recall) if (precision+recall) > 0 else 0.0

print("TP:", TP)
print("TN:", TN)
print("FP:", FP)
print("FN:", FN)
print("Precision:", precision)
print("Recall:", recall)
print("F-value:", f_value)
