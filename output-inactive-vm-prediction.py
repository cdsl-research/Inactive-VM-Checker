#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import sys
from datetime import datetime
import statistics

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(BASE_DIR, "vm-status", "tmp")
DATA_DIR = os.path.join(BASE_DIR, "data")

VM_WITH_COMMON_IP_FILE = os.path.join(DATA_DIR, "vm-with-common-ip")
INACTIVE_VM_PREDICTION_FILE = os.path.join(DATA_DIR, "inactive-vm-prediction")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

# 実行時オプションで--clean-tmpが指定された場合はtmpファイル削除
clean_tmp = "--clean-tmp" in sys.argv
if clean_tmp:
    for f in glob.glob(os.path.join(TMP_DIR, "*.tmp")):
        os.remove(f)

# ---------------------------------------------------
# 1. {data/vm-with-common-ipに記載されたVM名}-LAST.tmpを取得しINTERVAL算出
#
# {VM名}-LAST.tmpのログイン時刻差分(分単位)を計算し、{VM名}-INTERVAL.tmpに書き込む
# 先頭行はTIMESTAMPとの差分
#
# wtmp行が出る場合も考慮して、ログの解析は柔軟に対応。
# ここでは簡易的な処理例を示す。
# ---------------------------------------------------

def parse_datetime_from_line(line):
    # line内の日付時刻をパースする例(実際にはlastコマンド形式による詳細なパースが必要)
    # "Sat Dec 14 16:28 - 16:29"などから"Sat Dec 14 16:28"を抽出するといった処理が必要。
    # 本例では単純な正規表現マッチやsplitで対処を試みる(仮実装)。
    # 実際にはlastコマンドの出力フォーマットに合わせて正確にパースする必要あり。
    # wtmp行などはフォーマットが異なるが、適宜対応すること。
    # 以下は非常に簡易な仮実装:
    import re
    # 例: "c0a22100 pts/5 192.168.100.37 Sat Dec 14 16:28 - 16:29"
    # 日付以降を抽出: "Sat Dec 14 16:28"
    # wtmp行などは "wtmp begins Tue Nov 19 04:42:50 2024"
    # このように末尾に年がついたり、still runningなどがついたりする可能性がある。
    # 本例では "Mon|Tue|Wed|Thu|Fri|Sat|Sun" をキーにして日付抽出
    pattern = r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+([A-Za-z]{3})\s+(\d{1,2})\s+(\d{2}:\d{2})"
    match = re.search(pattern, line)
    if match:
        # 月英名->月数は固定テーブル
        month_map = {
            'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
            'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12
        }
        wday, month_str, day_str, time_str = match.groups()
        month = month_map[month_str]
        day = int(day_str)
        hour, minute = map(int, time_str.split(":"))
        # 年が明示されていないので今年と仮定(要件では特に指示なし)
        # 実際にはファイル内やTIMESTAMPからの推測が必要かもしれない。
        now_year = datetime.now().year
        return datetime(now_year, month, day, hour, minute)
    return None

def parse_timestamp_from_file(vm_name):
    # {VM名}-TIMESTAMP.tmpから基準となる時刻を取得すると仮定
    ts_file = os.path.join(TMP_DIR, vm_name + "-TIMESTAMP.tmp")
    if not os.path.exists(ts_file):
        return None
    with open(ts_file) as f:
        line = f.readline().strip()
        # 例: "Dec 14 22:22" のような形式を想定
        # 年は現行年を使う
        parts = line.split()
        # parts = ["Dec", "14", "22:22"]
        month_map = {
            'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
            'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12
        }
        if len(parts) == 3:
            month_str, day_str, time_str = parts
            month = month_map[month_str]
            day = int(day_str)
            hour, minute = map(int, time_str.split(":"))
            now_year = datetime.now().year
            return datetime(now_year, month, day, hour, minute)
    return None

with open(VM_WITH_COMMON_IP_FILE) as f:
    common_vms = [line.strip() for line in f if line.strip()]

for vm_name in common_vms:
    last_file = os.path.join(TMP_DIR, vm_name + "-LAST.tmp")
    if not os.path.exists(last_file):
        continue
    lines = [l.strip() for l in open(last_file).readlines() if l.strip()]

    timestamp_dt = parse_timestamp_from_file(vm_name)
    if not timestamp_dt:
        # TIMESTAMPがない場合はスキップ
        continue

    # 各行からログイン時間を抽出し、次行との差分をとる
    times = []
    for line in lines:
        dt = parse_datetime_from_line(line)
        if dt:
            times.append(dt)

    # INTERVAL計算: 
    # 一番最初はtimestamp_dtとの差分(分)
    # 2行目以降は(n+1行目時刻 - n行目時刻)を分で
    intervals = []
    if times:
        # 先頭はtimestampとの差分
        first_diff = (times[0] - timestamp_dt).total_seconds()/60.0
        intervals.append(first_diff)
        # 後続はログイン時刻間の差
        for i in range(1, len(times)):
            diff = (times[i] - times[i-1]).total_seconds()/60.0
            intervals.append(diff)

    interval_file = os.path.join(TMP_DIR, vm_name + "-INTERVAL.tmp")
    with open(interval_file, "w") as wf:
        for iv in intervals:
            wf.write(str(iv) + "\n")

# ---------------------------------------------------
# 2. c0a?????で始まるファイルごとにグルーピングし、4ファイル以上ある場合に四分位数計算
#    c0a?????-*-INTERVAL.tmp から平均値を取り、外れ値判定。
#    外れ値となったファイル名をinactive-vm-predictionへ追記。
# ---------------------------------------------------

# c0a?????形式で始まるINTERVALファイルを集計
interval_files = glob.glob(os.path.join(TMP_DIR, "c0a?????-*-INTERVAL.tmp"))

# グループ化
from collections import defaultdict
groups = defaultdict(list)
for fpath in interval_files:
    fname = os.path.basename(fpath)
    # c0a?????部分抽出
    prefix = fname.split("-")[0] # c0a22099 など
    groups[prefix].append(fpath)

with open(INACTIVE_VM_PREDICTION_FILE, "w") as wf:
    for prefix, files in groups.items():
        if len(files) >= 4:
            # すべてのファイルの平均値を求める
            mean_values = []
            file_mean_map = {}
            for fpath in files:
                vals = [float(x.strip()) for x in open(fpath).readlines() if x.strip()]
                if vals:
                    m = sum(vals)/len(vals)
                    mean_values.append(m)
                    file_mean_map[fpath] = m
                else:
                    file_mean_map[fpath] = 0.0

            if len(mean_values) < 4:
                # 平均値が4つ以上ないと四分位数計算が怪しいが、とりあえず計算
                pass

            # 四分位数計算
            mean_values_sorted = sorted(mean_values)
            Q1 = statistics.quantiles(mean_values_sorted, n=4)[0]  # 0.25分位
            Q3 = statistics.quantiles(mean_values_sorted, n=4)[2]  # 0.75分位
            IQR = Q3 - Q1
            threshold = Q1 + 1.5 * IQR

            # thresholdより小さいファイルをinactiveと判定
            for fpath, val in file_mean_map.items():
                # "valがthresholdより小さい"と指示文
                if val < threshold:
                    # ファイル名から"c0a?????-*"形式を抽出
                    # 実際にはVM名部分が"c0a22099-vm03"などになっているはずなので
                    # fname全体から"-INTERVAL.tmp"を除いたものを出力
                    base_vm_name = os.path.basename(fpath).replace("-INTERVAL.tmp", "")
                    wf.write(base_vm_name + "\n")
