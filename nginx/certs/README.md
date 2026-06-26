# TLS 憑證存放目錄

只有在「由本機 nginx 自行終結 TLS」時才需要用到這個目錄
（也就是 `.env` 設 `NGINX_CONF=nginx-ssl.conf`、`USE_HTTPS=true` 時）。

## 要放兩個檔

| 檔名 | 內容 |
|------|------|
| `fullchain.pem` | 伺服器憑證 + 中介憑證(chain)，依序串接 |
| `privkey.pem`   | 私鑰（最機密，**絕不可外洩、絕不可進版控**） |

## 從學校給的檔案產生 fullchain.pem

學校通常會給：伺服器憑證、中介憑證 / CA bundle、私鑰。

- 若是**分開的多個檔**：把「伺服器憑證」放最上面、「中介憑證」接在下面，串接成 `fullchain.pem`：
  ```bash
  cat your_server.crt intermediate.crt > fullchain.pem
  ```
- 若學校已給一個含完整鏈的檔，直接改名為 `fullchain.pem` 即可。
- 私鑰（申請時你自己產生的 `.key`）改名為 `privkey.pem`。

## 安全

- 本目錄的憑證與私鑰已被 `.gitignore` 排除（只有這份 README 會進版控）。
- 此專案若位於 Google Drive 同步資料夾，請確認私鑰不會被同步分享出去。
