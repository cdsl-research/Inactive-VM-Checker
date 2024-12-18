# Inactive-VM-Checker

概要  
VMのログインと他サーバとの通信の履歴から，使用していないVMを判断するコードです．

## スクリプト 
LASTコマンドとTCPDUMPコマンドの出力をsystemdで収集するシェルスクリプトです．  
  
```c0a22100-get-last-tcpdump.sh```  
```c0a22100-get-last-tcpdump.service```  
```c0a22100-get-last-tcpdump.timer```  

以下のコマンドを実行します．  
```
sudo systemctl daemon-reload
sudo systemctl enable c0a22100-get-last-tcpdump.timer
sudo systemctl start c0a22100-get-last-tcpdump.timer
```  

## output-vm-with-uncommon-ip.py  
共通しているIPアドレス以外のIPアドレスと通信しているVM名を出力するPythonスクリプトです．  
 
## output-inactive-vm-prediction.py  
ログイン履歴にもとづいて，使用されていないと判断されたVM名を出力するPythonスクリプトです．  
