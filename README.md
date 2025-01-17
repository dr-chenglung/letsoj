# letsoj
一個實用的OJ，適合基礎程式設計課程繳交作業與上機考試

![image](https://github.com/dr-chenglung/letsoj/blob/main/documents/contest-list.png)

# 系統建立
系統以 Django 開發，整個系統包含Django web, Postegres資料庫、Judge0判題系統、nginx以及gunicorn伺服器等。      

每個模組皆安裝運行在Docker容器(container)內。  

建議使用作業系統是Ubuntu20.02，Ubuntu系統可以安裝運行於Oracle VirtualBox虛擬機內，網路卡設定為"橋接介面卡"，在Ubuntu內設定好公開IP位址，可以進行考試IP管制。

若是使用Windows系統的Docker進行安裝也可以，但是OJ無法進行考試IP管制，其餘功能皆可正常運作。

# Judge0: 判題系統

[Judge0](https://github.com/judge0/judge0)是一個開源的線上判題系統，包含有Judge0 CE與Judge0 Extra CE兩種版本，兩種版本提供的程式語言不同。

[Judge0 Extra CE](https://github.com/judge0/judge0/tree/extra)提供的程式語言種類較少，包含Java, C, C++, C#, Python for ML等常見的初學者會學習的程式語言。

此OJ採用Judge0 Extra CE 的 [版本1.13.0](https://github.com/judge0/judge0/blob/master/CHANGELOG.md#deployment-procedur)。若需要其他未包含的程式語言判題，則必須修改程式改成使用Judge0 CE。

備註:  Judge0建議安裝於Ubuntu20.04，若安裝於Ubuntu22.04，必須修改其groups v1相容設定([連結](https://github.com/judge0/judge0/issues/325))
 
# 安裝
git clone https://github.com/dr-chenglung/letsoj.git  
cd letsoj  
docker compose up -d

# 管理者進入OJ系統
在瀏覽器輸入: localhost或是你的IP  

點選"登入"  

帳號 admin  
預設密碼: ojadmin 

注意: 登入後請立即修改管理者密碼

# 觀看OJ logs內容
docker compose logs -f

# 資料庫位置
在letsoj目錄下:  
oj-db/postgres

請定期經常備份資料庫，Ubuntu環境下，可以修改/etc/crontab檔案，進行定期備份到雲端硬碟。

# 匯入範例題目、語言、題目主題、使用者等表格

置放與範例資料表目錄中，匯入範例資料，可以快速熟悉OJ功能。

# 使用舊資料庫啟動OJ

請將你的舊資料庫放在letsoj目錄下:  
oj-db/postgres

重新啟動容器即可順利使用舊有或移轉的資料庫

可以下載範例資料庫壓縮檔(尚未提供)，解壓縮置放於oj-db目錄下，啟動後即可快速熟悉OJ所有的功能。

# 開發者程式碼

你可以啟動開發者模式，進行OJ系統程式開發  
docker compose -f docker-compose-dev.yml up -d

程式碼位置在letsoj目錄下:  
oj-web/

程式碼若有修改，gunicorn會自動重新啟動Django server，方便更新程式碼。

目前程式碼仍是雛型階段，功能未盡完善，或許存在潛在的Bugs。但已具備實用的OJ功能，尚能滿足基礎程式課程之繳交作業與考試的用途。可以依據個別需求加以修改或擴充。

# 管理者操作手冊
已置放在documents卷夾中，可下載參考。
