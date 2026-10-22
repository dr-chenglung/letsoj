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
docker compose up -d
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

正式環境部署前,請依序完成下列項目:

## 1. 關閉開發伺服器,改用 gunicorn
`docker-compose.yaml`:
```
DEV_SERVER: false   # 不啟動 python manage.py runserver,改用 gunicorn
```

## 2. 取消掛載本機原始碼
`docker-compose.yaml` 的 oj-web 服務:
```
volumes:
    # - ./oj-web:/app   # 正式環境請註解掉這行(避免本機程式碼覆蓋映像內容)
```

## 3. 重新建置映像(讓 requirements.txt 的套件版本生效)
升級套件(Django、requests 等)或改動需重裝依賴時,務必 rebuild:
```
docker compose build oj-web
docker compose up -d oj-web
```

## 4. 設定 .env(參考 .env.example)
- `DJANGO_SECRET_KEY`:一組夠長的隨機字串(切勿沿用範例值)
- `DJANGO_ALLOWED_HOSTS`:你的網域/IP(逗號分隔),務必包含伺服器對外 IP
- `DJANGO_DEBUG=false`:正式環境務必關閉

## 5. 啟用 HTTPS(建議)
若由本機 nginx 終結 TLS:
- `.env` 設 `NGINX_CONF=nginx-ssl.conf` 與 `USE_HTTPS=true`
- 憑證放到 `nginx/certs/`(`fullchain.pem`、`privkey.pem`,詳見 `nginx/certs/README.md`)

若 HTTPS 由上游代理處理,只需設 `USE_HTTPS=true`(nginx 仍用預設 `nginx.conf`)。

## 6. 更換 judge0 預設密碼與強化
- `judge0-v1.13.1/judge0.conf`:更換 `POSTGRES_PASSWORD`、`REDIS_PASSWORD` 的預設值
- 提交沙箱已預設 `ENABLE_NETWORK=false`(禁止提交程式對外連線)
- 若 judge0 需對外開放,建議設定 `AUTHN_TOKEN` 為 API 加上驗證

目前程式碼仍是雛型階段，功能未盡完善，或許存在潛在的Bugs。但已具備實用的OJ功能，尚能滿足基礎程式課程之繳交作業與考試的用途。可以依據個別需求加以修改或擴充。


# 管理者操作手冊
已置放在documents卷夾中，可下載參考。
