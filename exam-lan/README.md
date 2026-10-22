# 區域網路上機考試模式 (Windows + Docker Desktop)

## 為什麼需要這個模式

Windows 的 Docker Desktop 會把學生連線的來源 IP 改寫成 Docker 內部的閘道 IP，
Django 因此看不到學生電腦的真實 IP，「IP 限制」與「一 IP 一帳號」都會失效。

考試模式的做法是在 Windows 本機多架一個 nginx 當最外層入口：

```
學生電腦 (192.168.0.x)
   → Windows 本機 nginx (port 80，看得到真實 IP，寫入 X-Real-IP)
   → Docker 的 oj-nginx (只開在 127.0.0.1:8080，信任上一層的 X-Real-IP)
   → Django (oj-web)
```

一般模式完全不受影響：原本的 `docker-compose.yaml`、`nginx/nginx.conf`、`nginx/nginx-ssl.conf` 都沒有修改。

## 相關檔案

| 檔案 | 用途 |
|---|---|
| `docker-compose.exam.yaml` | 覆蓋檔：oj-nginx 改綁 `127.0.0.1:8080`，並改用 `nginx-exam.conf` |
| `nginx/nginx-exam.conf` | 容器內 nginx 設定：信任 Windows nginx 傳來的真實 IP |
| `exam-lan/windows-nginx/conf/nginx.conf` | Windows 本機 nginx 設定 |

## 第一次準備 (只需做一次)

1. **下載 nginx for Windows**：到 <https://nginx.org/en/download.html> 下載 Stable 版 zip，
   解壓到例如 `C:\nginx`。
2. **覆蓋設定檔**：只把 `exam-lan/windows-nginx/conf/nginx.conf` 這一個檔案複製到 `C:\nginx\conf\nginx.conf`，
   不要用整個 `conf` 資料夾去取代 `C:\nginx\conf` (裡面原本的其他檔案保留即可)。
   改完後在 `C:\nginx` 執行 `.\nginx.exe -t` 確認出現 `syntax is ok`。
3. **伺服器設定固定 IP**：在 Windows 網路設定把 OJ 伺服器設為固定 IP (例如 `192.168.0.10`)，
   或在 Router 設定 DHCP 保留。
4. **加入允許的 Host**：在 `.env` 的 `DJANGO_ALLOWED_HOSTS` **追加**伺服器的區網 IP
   (例如 `,192.168.0.10`)，原有的項目不要刪除。
5. **Windows 防火牆**：允許 `C:\nginx\nginx.exe` 的連入連線 (第一次啟動時跳出的視窗按「允許」，
   網路類型勾「私人」)。
6. **Router**：關閉 Wi-Fi，避免學生手機連進考試網段。

## 每次考試：切換到考試模式

在專案根目錄 (有 `docker-compose.yaml` 的那層) 執行：

```powershell
# 1. 以考試模式重啟容器 (oj-nginx 改綁 127.0.0.1:8080，讓出 80 port)
docker compose -f docker-compose.yaml -f docker-compose.exam.yaml up -d

# 2. 啟動 Windows 本機 nginx
cd C:\nginx
start nginx
```

學生用 `http://<伺服器區網IP>/` 連線 (例如 `http://192.168.0.10/`)。

## 驗證是否看得到真實 IP

讓兩三台教室電腦登入 OJ，再到管理後台查看「登入歷史記錄」：

- IP 各不相同，且都是 `192.168.0.x`：成功。
- IP 全部一樣 (例如 `172.x.x.1` 或 `192.168.65.x`)：學生沒有經過 Windows nginx，
  請確認 Windows nginx 有在執行、容器是用考試模式啟動的。

## 開啟考試模式 IP 綁定

到管理後台「考試管理」頁面：

1. **確認伺服器看得到真實 IP**：用一台**教室電腦**登入管理者帳號開啟此頁，
   「伺服器看到你目前的IP」應顯示 `192.168.0.x`。若出現紅字警告 (Docker/本機內部位址)，
   代表網路設定沒做好，此時開啟 IP 綁定會擋住所有考生。
2. 按「清除所有綁定與被拒紀錄」，清掉上一次考試的資料 (會同時登出所有考生)。
3. 打開「考試模式：IP 綁定」開關。打開時會**自動登出所有考生**，考生重新登入的那台電腦就會被綁定。

綁定只在**登入時**檢查。為了不讓綁定之前就存在的登入狀態繞過檢查，以下三個動作都會登出相關考生
(管理者不受影響)：打開開關、清除所有綁定、解除單一考生。

考試中：

- 考生第一次登入的電腦會被綁定；換電腦、或同一台電腦用其他瀏覽器登入別的帳號都會被拒絕，
  並出現在「被拒紀錄」。
- 考生電腦故障要換機時，在「綁定名單」找到他按「解除」(會同時登出他)，他到新電腦重新登入即可。
- **考試中請勿切換開關**：關閉期間任何人都能在任何電腦登入任何帳號；再打開時會登出全班。
- 管理者帳號不受綁定限制。

完整的操作步驟也寫在後台頁面上方的「區域網路上機考試操作指南」(點開即可查看)。

考試結束後關閉開關 (綁定資料留著無妨，下次開考前再清除即可)。

## 考試結束：回到一般模式

```powershell
# 1. 關閉 Windows 本機 nginx
cd C:\nginx
.\nginx.exe -s quit

# 2. 以一般模式重啟容器 (恢復 80/443)
docker compose up -d
```

## 常見問題

- **Windows nginx 啟動失敗，log 顯示 port 80 被占用**：通常是容器還在一般模式 (仍占用 80)，
  請先做「切換到考試模式」的第 1 步。也可能是 IIS 或其他服務占用，可用
  `netstat -ano | findstr :80` 查出是哪個程式。
- **學生看到 400 Bad Request**：伺服器區網 IP 沒有加進 `DJANGO_ALLOWED_HOSTS`。
- **考試模式只支援 http**：區網考試不需要 https；若要 https，需另外在 Windows nginx 設定憑證。
