# Inactive-VM-Checker

## 概要  
VMのログインと他サーバとの通信の履歴から，使用していないVMを判断するコードです．

## 1. スクリプト 
LASTコマンドとTCPDUMPコマンドの出力をsystemdで収集するシェルスクリプトです．  
  
```c0a22100-get-last-tcpdump.sh```  
```c0a22100-get-last-tcpdump.service```  
```c0a22100-get-last-tcpdump.timer```  

### 実行コマンド
使用されているか判断したいVMで，以下のコマンドを実行します．  
```
sudo systemctl daemon-reload
sudo systemctl enable c0a22100-get-last-tcpdump.timer
sudo systemctl start c0a22100-get-last-tcpdump.timer
```

### 実行結果
![image](https://github.com/user-attachments/assets/044b4e60-44f8-4b31-bd00-e7b5f4d93ed9)

```{VM名のホスト名}-LAST```ファイルの内容
```
c0a22100 pts/0        192.168.100.37   Tue Nov 19 08:46 - 10:02  (01:15)
c0a22100 pts/1        192.168.100.117  Tue Nov 19 04:59 - 04:59  (00:00)
c0a22100 pts/0        192.168.100.117  Tue Nov 19 04:54 - 05:01  (00:07)
c0a22100 pts/0        192.168.100.117  Tue Nov 19 04:47 - 04:49  (00:02)
reboot   system boot  6.8.0-49-generic Tue Nov 19 04:42   still running
wtmp begins Tue Nov 19 04:42:50 2024
```
```{VMのホスト名}-TCPDUMP```ファイルの内容
```
192.168.100.207 
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on ens34, link-type EN10MB (Ethernet), snapshot length 262144 bytes
16:30:00.265545 IP 192.168.100.207.60752 > 192.168.100.101.22: tcp 88
16:30:00.265578 IP 192.168.100.101.22 > 192.168.100.207.60752: tcp 0
16:30:00.270455 IP 192.168.100.101.22 > 192.168.100.207.60752: tcp 1112
```

## 2. Pythonスクリプト
### output-vm-with-uncommon-ip.py  
共通しているIPアドレス以外のIPアドレスと通信しているVM名を出力するPythonスクリプトです．  
 
### output-inactive-vm-prediction.py  
ログイン履歴にもとづいて，使用されていないと判断されたVM名を出力するPythonスクリプトです．  

### 実行コマンド  
![image](https://github.com/user-attachments/assets/7662ed12-9cb1-4bde-892f-aa4190b77910)

## 実行結果  
```output-vm-with-uncommon-ip.py ```実行時に出力される  
各VMの```{VMのホスト名}-VM-TCPDUMP```ファイルに共通して記録されているIPアドレス以外との通信が存在するVMのホスト名を記録する```diff-ip-vm```ファイルの内容  
  
![image](https://github.com/user-attachments/assets/2fcc1fe6-5e10-43fe-871a-b88644283736)


```output-inactive-vm-prediction.py```実行時に出力される使用されていないと判断するVMのホスト名のリストが記録される```inactive-vm-prediction```ファイルの内容  
  
![image](https://github.com/user-attachments/assets/5e128dc9-d209-4395-a986-8f00f4ae91fc)
