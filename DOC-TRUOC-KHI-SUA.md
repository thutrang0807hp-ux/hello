# ĐỌC TRƯỚC KHI SỬA — FREELANCE DESK

Bản bàn giao ngày **12/10/2026** (UTC+7). Người dùng chuyển dự án sang một tài khoản Codex/ChatGPT khác. Tài khoản mới không có lịch sử chat cũ: hãy đọc file này, `AGENTS.md`, rồi đối chiếu mã nguồn trước khi sửa. Đây là **mã nguồn đầy đủ**, không chỉ ảnh hoặc bản demo. Không cần viết lại ứng dụng từ đầu.

## Bắt đầu trong 5 phút

1. Giải nén ZIP, mở thư mục `FreelanceDesk-Handoff` chứa `server.py`.
2. Dùng Python 3.10+ (khuyên 3.12). Windows mở `start-windows.bat`; Linux/macOS chạy `sh start.sh`. Chạy backend không mở trình duyệt: `python server.py`.
3. App chạy ở `http://127.0.0.1:8000`. Giữ CMD đang chạy. Cấu hình AI và kênh thông báo nằm trong **Hồ sơ & kết nối**; hộp thư nằm trong **Khách hàng → Mở thư Upwork**.
4. ZIP không có dữ liệu thật hay khóa: chạy lần đầu tạo thư mục `data` trống. Để phát triển, dùng dữ liệu mẫu và nhà cung cấp giả lập.
5. Trước khi sửa, chạy kiểm tra liên quan trong phần kiểm thử. Đọc yêu cầu người dùng mới để biết họ muốn sửa gì; nếu họ chưa giao thay đổi cụ thể, chỉ xác nhận đã hiểu dự án, không tự đổi thiết kế hoặc cơ chế gọi AI.

Ứng dụng không cần thư viện Python ngoài để chạy. Kiểm thử trình duyệt cần Playwright và Chromium; Node.js dùng cho kiểm thử JS. `.env.example` chỉ là mẫu; app không tự nạp `.env`. Cấu hình riêng được đọc bởi `local_config.py` hoặc biến môi trường.

## Các quyết định người dùng đã chốt — phải giữ khi sửa

- Giao diện, giải thích, kết quả AI bằng **tiếng Việt dễ hiểu**. Có thể giữ tên job gốc tiếng Anh. Tên ngày lễ có giải thích tiếng Việt; lịch có thể nhảy về hiện tại.
- Không đổi toàn bộ stack hoặc thiết kế lại tính năng ngoài phạm vi được giao. Trang phải gọn, ít chữ kỹ thuật trong thao tác thường ngày, có chế độ sáng/tối đọc rõ và dùng được trên điện thoại.
- **AI job chỉ chạy khi người dùng bấm.** Không tự chấm tất cả job lúc nhập, tải trang, rê chuột hoặc mở chi tiết. Người dùng quan tâm chi phí/token.
- Trước AI, dùng **điểm khách 1–5 sao tính bằng quy tắc** từ dữ liệu đã thu thập (sao Upwork, lịch sử thuê, tỷ lệ thuê, xác minh thanh toán). Thiếu dữ liệu phải nói thiếu, không đoán. Ngân sách là bộ lọc riêng. Việc lọc/chấm sao không gọi AI.
- Ngoài thẻ job chỉ có nút **Phân tích công việc**, không thêm lại nút Đánh giá AI độc lập. Trong dialog, nút **Phân tích bằng AI** ở trên; kết quả thu gọn mặc định, bấm mới sổ xuống. Nền phía sau tối/mờ nhẹ. Không mở cửa sổ khi rê chuột.
- Kết quả AI thành công lưu SQLite theo nội dung/model/phiên bản; mở lại dùng cache, không gọi API lần nữa. Job thay đổi làm cache cũ không còn phù hợp; chạy lại vẫn cần thao tác của người dùng. Không xóa kết quả thành công để gọi lại vô ích.
- Job mới tự tăng **vòng tròn đỏ có số trên favicon/tab**; không cần nhập số thủ công. Khi người dùng vào mục Công việc, đánh dấu cả lô job đã nhận là đã xem thông báo; không bắt họ mở từng job. Job đến sau vẫn tăng số mới.
- Proposal Studio có node và đường nối; AI viết/chắt lọc/chấm thư chạy theo thao tác. Không tự gửi proposal lên Upwork. Lưu thư đã gửi khi người dùng xác nhận đã gửi thật.
- Khóa AI, Slack, Telegram điền trên web, không bắt nhập bằng CMD mỗi lần khởi động. `configure-windows.bat` là công cụ tùy chọn; `start-windows.bat` không tự mở hàng loạt bảng cấu hình.
- Hộp thư chỉ xử lý **email thông báo khách nhắn qua Upwork**. Lọc/ghép khách không dùng AI; không cần vào Upwork để đọc phần nội dung có sẵn trong email. Không suy diễn email là toàn bộ lịch sử trò chuyện.
- Hộp thư gọn: trạng thái và nút chính trên cùng; bộ lọc **Tất cả / Chưa đọc / Chờ liên kết**; cấu hình Google và nhập `.eml` chỉ mở khi bấm. Thư đã ghép chỉ hiện khách + **Đổi khách**.
- Ghép cuộc trò chuyện với khách một lần bằng mã `room_…`; không ghép bừa vì trùng tên. Không tự khẳng định có hợp đồng hoặc đổi nhóm khách chỉ vì họ nhắn. Không suy đoán khách Ghost từ thiếu dữ liệu.
- Giữ nguyên dữ liệu người dùng khi cập nhật. Khi bàn giao chỉ chia sẻ mã nguồn/tài liệu, không chia sẻ `data`, API key hay token.

## Kiến trúc và file cần tìm

| Phần | File |
| --- | --- |
| HTTP API, auth, SQLite, webhook, worker | `server.py` |
| Khởi động trên máy cá nhân | `run.py`, `start-windows.bat`, `start.sh` |
| Cấu hình riêng và công cụ cấu hình | `local_config.py`, `configure.py` |
| OpenAI Responses / Gemini GenerateContent, lỗi/quota/model | `ai_provider.py`, `services.py` |
| Chấm AI job và bản dữ liệu chấm | `job_radar.py` |
| Hoạt động khách trên job, vòng đời CRM | `job_activity.py`, `client_lifecycle.py` |
| Lọc job, tính sao không AI | `public/job-filters.js` |
| Danh sách job, dialog và cache AI | `public/jobs.js` |
| Điều hướng, polling, khách hàng, cài đặt, favicon | `public/app.js` |
| HTML, theme, CSS | `public/index.html`, `public/theme.js`, `public/style.css` |
| Node proposal, kho mẫu, tổng hợp thư | `public/studio.js`, `public/template-library.js`, `reference_synthesis.py`, `workflow.py` |
| Gmail OAuth, lọc/trích thư, chống trùng và ghép khách | `upwork_mail.py`, `public/upwork-mail.js` |
| Lịch Mỹ, trọng tâm tuần, thống kê, Excel | `public/us-context.js`, `public/focus.js`, `public/analytics.js`, `public/excel.js` |
| Bridge Chrome Toolkit | `toolkit-bridge/`, hai ZIP Toolkit trong `downloads/` |
| Tài liệu chi tiết | `README.md`, `HUONG-DAN-WINDOWS.txt`, `toolkit-bridge/README.md` |

Backend: Python stdlib, `ThreadingHTTPServer`, SQLite. Frontend: JS thuần, không React/npm build. Dữ liệu runtime Windows mặc định trong `%LOCALAPPDATA%\FreelanceDesk\data`, Linux/macOS là `data` cạnh mã nguồn. `FREELANCE_DATA_DIR` được ưu tiên. Module `data_store.py` thống nhất nơi lưu và sao chép data cũ nếu nơi mới còn trống, không xóa nguồn hoặc ghi đè đích đã có dữ liệu. Database là `workspace.sqlite3`; cấu hình riêng trong `data/local-config.json`, Gmail trong `data/gmail-private.json`, token webhook trong `data/webhook-token`. Không đưa các file này vào Git, log, export phát triển hoặc ZIP.

Polling web 10 giây, có tránh render lại khi dữ liệu không đổi. Gmail worker kiểm tra mỗi 120 giây khi máy chủ đang chạy và đã kết nối. Worker Slack/Telegram xử lý outbox có retry. Không chạy job AI tự động: `automatic_jobs()` luôn false. Biến AUTO_JOBS cũ không được dùng để bật lại.

## Tình trạng bàn giao và giới hạn thực tế

Mốc hộp thư trước bản sửa lưu trữ cố định: **`c933dd9`** trên repo `https://github.com/thutrang0807hp-ux/hello`. Gói này thêm tài liệu bàn giao và sửa các mô tả README đã lỗi thời; `HANDOFF-MANIFEST.json` ghi mốc lúc đóng gói và SHA-256 các file.

- Người dùng đã dùng được Toolkit nhận job vào app trên Windows. Bộ bridge đóng gói đã giữ các bundle gốc; đừng thay bằng một extension trắng chỉ có webhook.
- Người dùng báo OpenAI đã hoạt động ở phần viết thư. Không có khóa thật trong môi trường phát triển, vì vậy kiểm thử ở đây dùng giả lập, không chứng minh quota/model của tài khoản cụ thể.
- Gemini từng lỗi model ngừng hỗ trợ, HTTP 404/429/503. Có giao diện lấy danh sách model và chọn model. Không cam kết `gemini-2.5-flash` mặc định còn hoạt động cho mọi tài khoản; xác minh model Google trả về thay vì cứ khuyên dùng lại model đã lỗi.
- Gmail OAuth chỉ đọc đã triển khai: PKCE, state/cookie một lần, refresh token riêng, truy vấn thông báo 30 ngày gần đây, phân trang, không gửi/xóa thư. Google cấp scope `gmail.readonly` rộng hơn bộ lọc Upwork; **không nói scope này chỉ có quyền đọc thư Upwork**.
- Thư `.eml` có thể nhập thủ công để thử khi chưa cấu hình Google. Parser hiện nhắm mẫu tiếng Anh `sent you a message` từ `room_…@email.upwork.com`. Mẫu không trích được nội dung được báo rõ; chưa hỗ trợ mọi template/ngôn ngữ email Upwork.
- Google OAuth cá nhân cần bật Gmail API, tạo Client **Web application**, redirect đúng `http://127.0.0.1:8000/api/mail/callback` (cổng theo app), thêm Gmail vào Test users nếu Testing. Google có thể cho token Testing hết hạn sau 7 ngày.
- **Tại lúc bàn giao, người dùng đang lấy Client ID/Client Secret. Chưa xác nhận kết nối Gmail thật thành công.** Đã kiểm thử OAuth/đồng bộ bằng phản hồi giả lập và thao tác nhập thư trên backend thật; không được báo Gmail thật đã chạy.
- Nếu dán bản mới nhưng CMD còn chạy server cũ, nút hộp thư có thể không mở vì thiếu route/script mới. Bản mới đã hiện hướng dẫn: Ctrl+C CMD → chạy lại start-windows.bat → Ctrl+F5. Không xóa data để chữa lỗi.
- Linux cloud có Chromium managed chặn extension; không vượt chính sách để thử. Chrome extension và Tk dialog trên Windows cần kiểm thử trên máy Windows. Gói Toolkit có giấy phép GPL và mã nguồn tương ứng đi kèm.
- Một số bản demo/tài liệu ZIP cũ trong lịch sử có thể khác UI hiện tại. **Mã trong public và tài liệu bàn giao này là điểm xuất phát.** `demo.html` là dữ liệu mẫu, không chứng minh backend hoạt động. Gói bàn giao loại bỏ các ZIP cập nhật app cũ để tránh chép nhầm.

## Kiểm thử và bằng chứng

Tại bản bàn giao đã có **78 unit test Python** qua; smoke hộp thư, nhập/ghép/đọc, UI sáng/tối/mobile và lỗi sau cập nhật đã qua bằng Chromium + provider giả lập. Hãy đọc `HANDOFF-VALIDATION.txt` để biết các lệnh chạy lại và kết quả của lần đóng gói này. Không coi test giả lập là xác nhận một tài khoản thật đã kết nối.

```sh
python -m unittest discover -s tests -p 'test_*.py'
node tests/job_filters.test.js
node tests/job_customer_stars.test.js
node --check public/app.js
node --check public/jobs.js
node --check public/upwork-mail.js
```

Kiểm thử UI liên quan (cần Python Playwright + Chromium):

```sh
python tests/customer_stars_smoke.py
python tests/upwork_mail_smoke.py
python tests/upwork_mail_update_smoke.py
python tests/tab_badge_smoke.py
```

Các smoke dùng `/usr/bin/chromium` + `--no-sandbox` trong Linux hiện tại. Trên máy khác hãy đặt executable phù hợp; không chỉnh logic app để tránh lỗi môi trường test. Một số smoke lâu đời có thể còn giả định UI trước khi bỏ hover/đổi tên nút; xác minh assertion trước khi dùng chúng làm hợp đồng hiện tại. Không chạy API AI thật hoặc gửi tin Slack/Telegram thật chỉ để test.

## Cách cập nhật và tiếp tục làm việc

1. Đọc `AGENTS.md`, xác định file và yêu cầu liên quan; kiểm tra Git trước khi sửa.
2. Phát triển với thư mục dữ liệu riêng và mock. Không đọc khóa thật của người dùng để debug.
3. Kiểm thử hành vi thay đổi, tạo bản xem trước bằng dữ liệu mẫu khi thay UI. Không dùng ảnh thay cho mã chạy được.
4. Để cập nhật máy người dùng, đóng CMD, sao lưu data riêng trên máy đó, chép mã mới vào đúng thư mục, giữ data, chạy lại rồi Ctrl+F5.
5. Nếu thêm asset JS hoặc module Python, cập nhật HTML, route static trong server và danh sách file của gói phát hành. Thử từ ZIP được giải nén, không chỉ từ checkout.
6. Repo gốc có GitHub và lịch sử, nhưng tài khoản Codex mới có thể chưa có quyền push. ZIP vẫn sửa/chạy được mà không có GitHub; chỉ báo quyền còn thiếu nếu thao tác đó thật sự cần.

### Câu nhắn mẫu cho Codex tài khoản mới

> Đây là dự án Freelance Desk đang chạy trên Windows. Hãy giải nén mã nguồn, đọc DOC-TRUOC-KHI-SUA.md và AGENTS.md trước, rồi giữ các quyết định đã chốt. Không viết lại từ đầu, không tự gọi AI/gửi thông báo thật, không đọc hoặc chia sẻ data chứa khóa. Tôi muốn bạn sửa: [ghi thay đổi]. Sau khi sửa hãy kiểm thử phần liên quan và tạo bản xem trước/gói cập nhật, giữ dữ liệu cũ.

Cập nhật sau bàn giao ban đầu: đã kiểm thử HTTP lưu AI/Telegram và phiên Gmail giả lập, dừng server rồi khởi động lại từ CMD/cwd khác; cấu hình, bản ghi khách và token webhook vẫn giữ. Xem `tests/persistence_restart_smoke.py`. Lưu cùng Client ID/Secret không xóa phiên Gmail nữa. Kết nối Google thực tế vẫn phụ thuộc thời hạn/token Google.

Có choose-data-windows.bat/choose_data.py để chọn nơi lưu bằng Tk; location JSON không chứa khóa nhưng cũng không đóng gói. Bản sửa đóng SQLite bằng contextlib.closing trước rename (with sqlite3.connect chỉ commit, không close), tránh Windows giữ handle gây WinError 5. Kiểm thử khóa tệp giả lập và chọn vị trí đã qua; GUI Windows cần xác minh thực tế.
