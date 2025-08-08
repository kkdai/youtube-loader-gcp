# YouTube 字幕與資料載入器

這是一個基於 Flask 開發的應用程式，旨在從 YouTube 影片中提取字幕與中繼資料。它特別為部署在 Google Cloud Run 上進行了優化，並能處理任何公開的 YouTube 影片。

## 主要功能

- **提取影片字幕**：透過 `/load-youtube-transcript` 端點，使用影片 ID (`v_id`) 提取任何公開影片的字幕。
- **多語言支援**：預設會依序嘗試抓取英文 (`en`)、日文 (`ja`)、繁體中文 (`zh-TW`) 和簡體中文 (`zh-CN`) 的字幕。您也可以透過 `languages` 參數自訂語言順序 (例如：`languages=es,fr`)。
- **提取影片資訊**：透過 `/load-youtube-data` 端點，使用 `langchain_community` 函式庫獲取影片的詳細資訊 (標題、作者等)。
- **RESTful API**：提供簡單易用的 API 端點來獲取資料。
- **專為雲端設計**：可無縫部署至 Google Cloud Run 平台。

## 環境準備

在部署或本機執行前，請確保您已安裝以下工具：

- Python 3.7 或更高版本
- Google Cloud SDK (gcloud CLI)

## 本機執行與測試

1.  **複製專案**：
    ```bash
    git clone https://github.com/kkdai/gcp-test-youtuber.git
    cd gcp-test-youtuber
    ```

2.  **安裝依賴套件**：
    ```bash
    pip install -r requirements.txt
    ```

3.  **設定環境變數**：
    ```bash
    export PORT=8080
    # 如果要測試 /load-youtube-data，需要設定以下變數並在 Secret Manager 中準備好憑證
    export PROJECT_ID="YOUR_GCP_PROJECT_ID" 
    export GOOGLE_SECRET_KEY_YOUTUBE_API_CREDENTIALS='YOUR_SERVICE_ACCOUNT_JSON_CONTENT'
    ```

4.  **啟動應用程式**：
    ```bash
    python main.py
    ```

5.  **測試端點**：
    - 字幕：`curl "http://localhost:8080/load-youtube-transcript?v_id=KsYicre9mjg"`
    - 影片資訊：`curl "http://localhost:8080/load-youtube-data?v_id=KsYicre9mjg"`

## 部署到 Google Cloud Run

1.  **設定您的 Google Cloud 專案 ID**：
    ```bash
    export PROJECT_ID="YOUR_GCP_PROJECT_ID"
    gcloud config set project $PROJECT_ID
    ```

2.  **建置 Docker 映像檔並提交至 Google Container Registry**：
    ```bash
    gcloud builds submit --tag gcr.io/$PROJECT_ID/youtube-loader
    ```

3.  **部署應用程式至 Cloud Run**：
    ```bash
    gcloud run deploy youtube-loader \
      --image gcr.io/$PROJECT_ID/youtube-loader \
      --platform managed \
      --region asia-east1 \
      --allow-unauthenticated
    ```
    *   `--region`：您可以選擇離您最近的區域。
    *   `--allow-unauthenticated`：允許公開存取您的 API 端點。

4.  **存取您的服務**：
    部署成功後，gcloud 會提供一個服務 URL。您可以使用該 URL 來存取您的 API，例如：
    `https://youtube-loader-xxxxxxxx-an.a.run.app/load-youtube-transcript?v_id=VIDEO_ID`

## API 端點

- `GET /`
  - **功能**：健康檢查端點。
  - **回傳**：`Hello, World!`

- `GET /load-youtube-transcript`
  - **功能**：獲取指定影片的字幕。
  - **參數**：
    - `v_id` (必要)：YouTube 影片的 ID。
    - `languages` (可選)：用逗號分隔的語言代碼，例如 `ko,th`。若未提供，則使用預設值。
  - **成功回傳**：`{"transcript": "影片字幕文字..."}`
  - **失敗回傳**：`{"error": "錯誤訊息..."}`

- `GET /load-youtube-data`
  - **功能**：獲取影片的中繼資料。
  - **注意**：此端點需要正確設定服務帳號憑證 (`youtube_api_credentials`) 於 Secret Manager 中。
  - **參數**：
    - `v_id` (必要)：YouTube 影片的 ID。
  - **成功回傳**：`{"ids_data": "[Document(...)]"}`
  - **失敗回傳**：`{"error": "錯誤訊息..."}`