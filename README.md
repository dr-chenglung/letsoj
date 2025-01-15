# letsoj
一個實用的OJ，適合基礎程式設計課程繳交作業與上機考試

![image](https://github.com/dr-chenglung/letsoj/blob/main/extra-data/contest-list.png)

<h2>系統如何建立?</h2>
系統以 Django 開發，整個系統包含Django web, Postegres資料庫、Judge0判題系統、nginx以及gunicorn伺服器等    

每個模組皆安裝運行在Docker容器(container)內  

建議使用作業系統是Ubuntu20.02，Ubuntu系統安裝運行於Oracle VirtualBox虛擬機內。

若是使用Windows系統的Docker進行安裝也可以，但是OJ無法進行考試IP管制，其餘功能皆可正常運作。

# 安裝
git clone https://github.com/dr-chenglung/letsoj.git  
cd letsoj  
docker compose up -d

# 管理者進入OJ系統
在瀏覽器輸入: localhost或是你的IP  

點選"登入"  

帳號 admin  
預設密碼: adminoj 

注意: 登入後請立即修改管理者密碼

# 觀看OJ logs內容
docker compose logs -f

# 資料庫位置
在letsoj目錄下:  
oj-db/postgres

請定期經常備份資料庫，Ubuntu環境下，可以修改/etc/crontab檔案，進行定期備份到雲端硬碟。

# 使用舊資料庫啟動OJ

請將你的舊資料庫放在letsoj目錄下:  
oj-db/postgres

重新啟動容器即可順利使用舊有或移轉的資料庫

# 開發者程式碼

你可以啟動開發者模式，進行OJ系統程式開發  
docker compose -f docker-compose-dev.yml up -d

程式碼位置在letsoj目錄下:  
oj-web/

程式碼若有修改，gunicorn會自動重新啟動Django server，方便更新程式碼。

目前程式碼仍是雛型階段，功能也未盡完善，但已具備實用的OJ功能，尚能滿足基礎程式課程之繳交作業與考試的用途。

# 管理者操作手冊
