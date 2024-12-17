#!/bin/bash

# ファイルを作成する
FILE_NAME="/c0a22100-get-last-tcpdump/c0a22100-$(hostname)-last-tcpdump.txt"
sudo echo -n "" > "$FILE_NAME"

# 実行日時を追記する
echo "$(date '+%b %d %H:%M')" >> "$FILE_NAME"
echo "" >> "$FILE_NAME"

# kubectlが実行できるか追記する
if kubectl version --client > /dev/null 2>&1; then
    echo "true" >> "$FILE_NAME"
else
    echo "false" >> "$FILE_NAME"
fi
echo "" >> "$FILE_NAME"

# lastの実行結果から空行を除いて追記する
last | sed '/^\s*$/d' >> "$FILE_NAME"
echo "" >> "$FILE_NAME"

# tcpdump
# ホスト名に対応するIPアドレスを取得する
SERVER_IPS=$(hostname -I | awk '{for(i=1; i<=NF; i++) print $i}')
# ホスト名に対応するIPアドレスが複数ある場合は，IPアドレスを結合する
TCPDUMP_FILTER=$(echo "$SERVER_IPS" | awk '{printf (NR>1 ? " or host %s" : "host %s"), $1}')
# tcpdumpの実行結果を追記する
if [ -n "$TCPDUMP_FILTER" ]; then
    echo "$(hostname -I)" >> "$FILE_NAME"
    # 実行する秒数を指定する(.timerファイルも対応して修正する必要がある)
    timeout 600 sudo tcpdump -n -q "$TCPDUMP_FILTER" >> "$FILE_NAME" 2>&1
else
    echo "Failed to retrieve server IP addresses." >> "$FILE_NAME"
fi

# scpで記録ファイルをリモートサーバにコピーする
scp -i /c0a22100-get-last-tcpdump/c0a22100-key -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$FILE_NAME" c0a22100@vm02:/home/c0a22100/Inactive-VM-Checker/vm-last-tcpdump/${FILE_NAME#"/c0a22100-get-last-tcpdump/c0a22100-"}