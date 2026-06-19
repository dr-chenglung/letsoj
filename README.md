# letsoj
一個實用的OJ，適合基礎程式設計課程繳交作業與上機考試

![image](https://github.com/dr-chenglung/letsoj/blob/main/documents/contest-list.png)

# 系統建立
系統以 Django 開發，整個系統包含Django web, Postegres資料庫、Judge0判題系統、nginx以及gunicorn伺服器等。      

每個模組皆安裝運行在Docker容器(container)內。  

Judge0建議安裝於Ubuntu20.04，若安裝於Ubuntu22.04，必須修改其groups v1相容設定([連結](https://github.com/judge0/judge0/issues/325))

若是使用Windows系統的Docker進行安裝也可以，但是OJ無法進行考試IP管制，其餘功能皆可正常運作。

若使用Windows作業系統，需要進行IP管制，建議將Ubuntu安裝運行於Oracle VirtualBox虛擬機內，網路卡設定為"橋接介面卡"，在Ubuntu內設定好公開IP位址(可與Host不同IP)，就可以進行考試IP管制。

# Judge0: 判題系統

[Judge0](https://github.com/judge0/judge0)是一個開源的線上判題系統，包含有Judge0 CE與Judge0 Extra CE兩種版本，兩種版本提供的程式語言不同。

此OJ採用Judge0 CE 的 [版本1.13.1](https://github.com/judge0/judge0/blob/master/CHANGELOG.md#deployment-procedur)。

 
# 安裝
```
git clone https://github.com/dr-chenglung/letsoj.git  
cd letsoj  
docker compose up
```
或是多個判題容器
```
docker compose up --scale workers=3
```
# 觀看OJ logs內容
```
docker compose logs -f
```
# 先要修改你的.env (參考.env.example)
所有的帳號與密碼要寫在環境檔案裡面

# 資料庫位置
在letsoj目錄下:  
oj-postgres-db/postgres

請定期經常備份資料庫，Ubuntu環境下，可以修改/etc/crontab檔案，進行定期備份到雲端硬碟。

# 程式碼位置在letsoj目錄下
oj-web/

# 匯入範例題目、語言、題目主題、使用者等表格

置放與範例資料表目錄中，匯入範例資料，可以快速熟悉OJ功能。

# 使用舊資料庫啟動OJ

請將你的舊資料庫放在letsoj目錄下:  
oj-postgres-db/postgres

重新啟動容器即可順利使用舊有或移轉的資料庫

可以下載範例資料庫壓縮檔(尚未提供)，解壓縮置放於oj-postgres-db目錄下，啟動後即可快速熟悉OJ所有的功能。

# 正式佈署

可修改docker-compose.yaml
```
DEV_SERVER: false # 不會啟動python manage.py runserver
```
將oj-web 加上註解如下:
```
volumes
    # - ./oj-web:/app  # 將這行加上註解
```

目前程式碼仍是雛型階段，功能未盡完善，或許存在潛在的Bugs。但已具備實用的OJ功能，尚能滿足基礎程式課程之繳交作業與考試的用途。可以依據個別需求加以修改或擴充。


# 管理者操作手冊
已置放在documents卷夾中，可下載參考。
