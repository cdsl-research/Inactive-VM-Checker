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

## 2. Pythonスクリプト
### output-vm-with-uncommon-ip.py  
共通しているIPアドレス以外のIPアドレスと通信しているVM名を出力するPythonスクリプトです．  
 
### output-inactive-vm-prediction.py  
ログイン履歴にもとづいて，使用されていないと判断されたVM名を出力するPythonスクリプトです．  

### 実行コマンド  
![image](https://github.com/user-attachments/assets/7662ed12-9cb1-4bde-892f-aa4190b77910)

## 実行結果  
![スクリーンショット 2024-12-20 054026](https://github.com/user-attachments/assets/eeeaf1f5-3569-4448-9513-dc8bfe8f5954)
