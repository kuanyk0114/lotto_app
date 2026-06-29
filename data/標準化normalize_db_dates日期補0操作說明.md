請問我想將備份的lotto\_history.db日期也一併標淮化要如何使用normalize\_db\_dates.py

下午4:24





我已經將 

normalize\_db\_dates.py

&#x20;改寫為支援自訂命令列參數的通用版本，並將最新代碼推送至 GitHub 同步。



現在，您可以在終端機（Powershell 或 CMD）中非常簡單、安全地執行它來處理您任何位置的備份資料庫。



💡 執行方式

在專案根目錄下，執行以下指令並在後方帶上您備份資料庫的檔案路徑即可：



bash





python data/normalize\_db\_dates.py "您備份資料庫的檔案路徑"

範例：

如果您備份的資料庫檔案位在 D:\\backup\\lotto\_history\_old.db：



bash





python data/normalize\_db\_dates.py "D:\\backup\\lotto\_history\_old.db"

🛡️ 運作特點

自動備份：腳本執行時會先在該備份檔的同目錄下，自動複製產生一份 .bak 備份檔（例如 D:\\backup\\lotto\_history\_old.db.bak），確保您的資料安全。

就地更新：備份完成後，腳本會直接更新指定路徑的資料庫，將所有彩種的日期補零，一次搞定！

