BÀN GIAO SANG CODEX KHÁC: đọc BAN-GIAO-HIEN-TAI.md và dùng PROMPT-CHO-CODEX-MOI.txt. Gói nguồn đầy đủ có bộ cài desktop; không kèm dữ liệu/khóa riêng.

# Freelance Desk

**Bàn giao cho Codex/tài khoản khác:** đọc [DOC-TRUOC-KHI-SUA.md](DOC-TRUOC-KHI-SUA.md) trước. ZIP bàn giao chứa mã nguồn và kiểm thử, không chứa thư mục dữ liệu hay khóa.

Web dùng riêng cho freelancer: quản lý khách hàng, nhận job từ Upwork Toolkit trên Chrome, soạn proposal bằng AI và nhận thông báo trong web, Slack, Telegram.

## Tải về và chạy trên Windows

1. Trên GitHub, chọn **Code → Download ZIP**, sau đó giải nén toàn bộ.
2. Cài [Python 3.12](https://www.python.org/downloads/windows/), tích **Add python.exe to PATH**.
3. Mở **start-windows.bat** để chạy app. AI, Slack và Telegram cấu hình trong web; công cụ configure-windows.bat chỉ mở khi bạn chủ động chọn.
4. Trình duyệt tự mở ứng dụng. Giữ cửa sổ chạy app mở trong lúc dùng.

Hướng dẫn chi tiết: [HUONG-DAN-WINDOWS.txt](HUONG-DAN-WINDOWS.txt). **demo.html** chỉ là mô phỏng; muốn lưu dữ liệu thật, chạy **start-windows.bat**. AI hỗ trợ Gemini và OpenAI; Muse chưa được tích hợp.

## Chạy

Python 3.10+; ứng dụng không cần gói ngoài.

**Máy cá nhân (lựa chọn hiện tại):** tải và giải nén gói ứng dụng. Mở `demo.html` để xem thử thiết kế và thao tác bằng dữ liệu / AI mẫu, không cần Python; tải lại demo sẽ đặt lại dữ liệu. Windows: cài Python 3.10+ từ python.org, bật tùy chọn thêm Python vào PATH, rồi mở `start-windows.bat`. macOS/Linux: chạy `sh start.sh` trong thư mục ứng dụng. Trình duyệt sẽ tự mở; giữ cửa sổ chạy ứng dụng và Chrome đang dùng Upwork Toolkit hoạt động.

Khi chủ động mở công cụ cấu hình, công cụ hỏi mật khẩu riêng, khóa AI và cấu hình Slack/Telegram. Có thể nhấn Enter để bỏ qua kênh chưa dùng; token và mật khẩu không hiển thị khi nhập. Các giá trị được lưu trong `data/local-config.json`, không mã hóa, với quyền tệp riêng trên hệ thống hỗ trợ. Giữ kín thư mục này. Để chỉnh cấu hình: Windows mở `configure-windows.bat`; macOS/Linux chạy `python3 configure.py`, rồi khởi động lại ứng dụng. Enter giữ giá trị cũ; dấu `-` xóa một giá trị.

Chạy máy chủ thủ công (không mở trình duyệt):

```sh
cd /workspace/hello
python3 server.py
```

Mặc định máy chủ chạy nội bộ ở cổng 8000. `PORT` đổi cổng. `FREELANCE_DATA_DIR` đổi thư mục lưu dữ liệu, mặc định trên Windows là `%LOCALAPPDATA%\FreelanceDesk\data` (dùng APPDATA nếu không có LOCALAPPDATA); Linux/macOS là `data/` cạnh mã nguồn. Sao lưu toàn bộ thư mục dữ liệu khi máy chủ đã dừng, gồm SQLite và token webhook. Nút xuất JSON xuất các bản ghi để bạn lưu thêm; chưa có chức năng nhập lại JSON.

## Luồng làm việc

1. Nhập dịch vụ, kinh nghiệm thực tế và portfolio tại **Hồ sơ & kết nối**.
2. Nối Webhook từ Upwork Toolkit để job mới xuất hiện trong **Cơ hội công việc**.
3. Chọn **Phân tích công việc** để đọc mô tả và thông tin khách; nếu thiếu nội dung, dùng **Bổ sung mô tả**. Vào tab **Proposal Studio**, chọn job trong node thông tin công việc để soạn thư.
4. Nối node job và các node mẫu vào thư nháp; nhập cách giải quyết, giá, thời hạn và nhấn viết AI.
5. Chạy node **AI đánh giá**, xem điểm / điểm mạnh / điểm yếu, rồi hoàn thiện node **Thư cuối**.
6. Sao chép thư để gửi trên Upwork. Sau khi thực sự gửi, chọn **Tôi đã gửi → Lưu vào kho**; cập nhật kết quả ở **Thư đã gửi**.

AI viết/chấm thư và chấm job chỉ được gọi khi bạn nhấn nút. Job có điểm khách 1–5 sao tính bằng quy tắc miễn phí trước khi dùng AI. Bấm **Phân tích công việc**, rồi **Phân tích bằng AI** để chấm; kết quả thành công được lưu, mở lại dùng cache. Không gọi AI khi rê chuột hoặc tải danh sách. Hồ sơ, mô tả job và thông tin thư được gửi tới nhà cung cấp bạn chọn. OpenAI dùng Responses API với `store: false`; Gemini dùng GenerateContent API. Gemini có mức miễn phí cho một số model/tài khoản, có giới hạn và thay đổi theo chính sách Google; ứng dụng không cam kết mọi lượt gọi miễn phí. OpenAI API tính phí riêng. Ứng dụng không tự gửi proposal lên Upwork.

## Cấu hình AI, Slack và Telegram

Trên máy cá nhân, dùng công cụ cấu hình như hướng dẫn phía trên. Không cần Publish môi trường cloud để chạy trên máy bạn. Nếu sau này chạy trong Codex cloud, các yêu cầu dưới đây cũng đã được lưu vào cấu hình nháp; nhập giá trị qua cài đặt môi trường, lưu và Publish rồi khởi động lại ứng dụng. Không gửi khóa trong chat hoặc commit vào Git. Người dùng kỹ thuật có thể truyền các biến tương ứng qua môi trường của tiến trình; giá trị đã có trong môi trường được ưu tiên hơn cấu hình local. Mẫu tên biến có trong `.env.example` (ứng dụng không tự đọc tệp `.env`).

| Biến | Công dụng |
| --- | --- |
| `FREELANCE_AI_PROVIDER` | `gemini` hoặc `openai`; cấu hình cũ thiếu biến này vẫn dùng OpenAI |
| `FREELANCE_AI_KEY` | Khóa API của nhà cung cấp đã chọn; chỉ gửi trong header, không nằm trong URL/web |
| `FREELANCE_AI_MODEL` | Để trống: Gemini dùng `gemini-2.5-flash`, OpenAI dùng `gpt-4.1-mini` |
| `FREELANCE_AI_AUTO_JOBS` | Thiết lập cũ, không còn bật tự chấm. AI chỉ chạy khi bấm **Đánh giá AI** để kiểm soát credit. |
| `FREELANCE_SLACK_TOKEN` | Bot token của Slack app, dùng với `slack.com` |
| `FREELANCE_SLACK_CHANNEL` | ID kênh Slack nhận job |
| `FREELANCE_TELEGRAM_TOKEN` | Bot token Telegram, dùng với `api.telegram.org` |
| `FREELANCE_TELEGRAM_CHAT_ID` | ID cuộc trò chuyện nhận job |
| `FREELANCE_PASSWORD` | Mật khẩu đăng nhập web, được đọc trực tiếp bởi máy chủ |
| `FREELANCE_COOKIE_SECURE` | Đặt `1` khi truy cập qua HTTPS |
| `FREELANCE_BIND` | Mặc định `127.0.0.1`; địa chỉ bên ngoài chỉ được chấp nhận khi có mật khẩu |
| `FREELANCE_WEBHOOK_TOKEN` | Tùy chọn: token dài tối thiểu 24 ký tự; mặc định ứng dụng tự tạo và giữ trong `data/` |

Gemini trên Windows: mở `configure-windows.bat`, chọn **1 = Gemini**, tạo khóa tại [Google AI Studio](https://aistudio.google.com/apikey), dán khóa khi được hỏi, để trống model để dùng mặc định rồi khởi động lại app. Khóa không hiện khi dán. Kiểm tra model/quota của tài khoản trong AI Studio; có thể nhập tên model khác mà tài khoản hỗ trợ. Chọn nhà cung cấp khác sẽ xóa khóa/model cũ khỏi cấu hình đang dùng để tránh gửi nhầm khóa. Nhấn Enter giữ mật khẩu và các token thông báo đã có.

Gemini hỗ trợ viết thư, sửa đoạn được chọn, chấm thư, chắt lọc toàn bộ kho mẫu theo batch và chấm job. Quota lỗi báo rõ, không tự chuyển sang API khác. Chắt lọc kho lớn có thể cần nhiều lượt gọi; các lượt đã xử lý vẫn có thể tiêu quota nếu bước sau thất bại. Chỉ phản hồi kết thúc hoàn chỉnh được áp dụng; nội dung nháp cũ được giữ khi lỗi.

Kiểm chứng giao thức Gemini dựa trên SDK chính thức [googleapis/python-genai](https://github.com/googleapis/python-genai), gồm `responseJsonSchema` cho kết quả có cấu trúc. Kiểm thử dùng phản hồi mô phỏng cho cả hai nhà cung cấp và các endpoint ứng dụng; chưa xác nhận bằng khóa Gemini thật.

Slack: tạo Slack app trong workspace của bạn, thêm quyền bot `chat:write`, cài app vào workspace và mời bot vào kênh nhận thông báo. Lấy bot token và channel ID trong cấu hình Slack. Telegram: tạo bot qua BotFather, gửi `/start` cho bot, lấy chat ID bằng `getUpdates` hoặc công cụ quản trị của bạn. Token được giữ phía máy chủ, không đưa vào giao diện web.

Khi hai biến của một kênh đã có, job mới sẽ được đưa vào hàng đợi của kênh đó. Job cũ không được gửi lại khi bạn mới cấu hình kênh. Thông báo lỗi được thử lại tối đa 5 lần với thời gian chờ tăng dần; lịch sử và nút thử lại nằm trong **Hồ sơ & kết nối**. Trường hợp mạng bị ngắt sau khi nhà cung cấp đã nhận thông báo có thể tạo thông báo lặp khi thử lại; chống trùng job trong cơ sở dữ liệu vẫn được giữ.

## Nối với Upwork Toolkit

Bản Chrome Web Store 1.6.0 người dùng cung cấp không có Mobile alerts/Webhook. Gói [Toolkit-Installed-Build-Bridge.zip](downloads/Toolkit-Installed-Build-Bridge.zip) giữ các bundle lấy job của đúng bản đó, thêm cầu nối đọc job đã lưu trong `chrome.storage.local.__JOBS` và gửi tới Freelance Desk trên cùng máy. Không thêm yêu cầu tới Upwork, không đọc cookie/khóa AI, không đổi lịch lấy job. Cầu nối gửi dữ liệu ngay khi cache cập nhật, không phụ thuộc lịch thông báo desktop.

1. Giải nén gói, tắt các bản Toolkit khác (giữ lại để quay về), bật Developer mode ở `chrome://extensions`, Load unpacked thư mục `toolkit-desk-bridge` có `manifest.json`.
2. Bấm biểu tượng chữ U của bản cầu nối (hoặc Extension options) để mở thẳng trang kết nối.
3. Mở web bằng `start-windows.bat`, vào **Hồ sơ & kết nối**, sao chép URL; dán vào trang cầu nối và bấm **Lưu & kết nối**.
4. Khi Toolkit có job, kiểm tra tab **Công việc**. Nút **Gửi job hiện có** dùng job thật trong cache, không tạo job mẫu.
5. Giữ Chrome và web mở. Hàng đợi lưu bền, thử lại mỗi phút; giới hạn 500 job / khoảng 4 MB và báo khi đầy. Web chống trùng ID khi gửi lại.

Bản sao có ID riêng, không tự chuyển cài đặt hay lịch sử từ bản cũ; chọn lại Feed source/lịch/âm thanh trong Settings. Chỉ cache của bản sao được chuyển (Toolkit giữ tối đa 50 job hiện tại). Cầu nối này chỉ chấp nhận URL `http://127.0.0.1` hoặc `http://localhost`. Việc dùng Toolkit và quy định Upwork không được xác nhận bởi các kiểm thử cầu nối.

Hướng dẫn đầy đủ: [INSTALL-WINDOWS.txt](toolkit-bridge/INSTALL-WINDOWS.txt). Mã cầu nối/đóng gói: [toolkit-bridge](toolkit-bridge). Mã nguồn gốc bản Web Store theo release ID `4be0325640df585fb9030a5ddffa756ea0effce0`: [source ZIP](downloads/Toolkit-Installed-Build-Source.zip), từ [neeilya/upwork-toolkit](https://github.com/neeilya/upwork-toolkit), GPL-3.0.

Bản GitHub khác tại commit `e75003468d373353e69ff46c1c54cec02100ae41` có **Mobile alerts → Webhook** sẵn. Nếu đang dùng bản đó: dán URL → Save/cấp quyền → bật Webhook → Send test. Không bật đồng thời với bản cầu nối để tránh hai bản cùng lấy job.

Nếu chạy web trên máy cá nhân cùng Chrome, địa chỉ nội bộ trong phần kết nối dùng được trên máy đó. Nếu chạy web trên máy chủ, cần địa chỉ HTTPS mà Chrome trên máy bạn truy cập được. **Publish môi trường Codex không tự tạo địa chỉ web công khai.**

Ứng dụng này nhận JSON từ tiện ích, không gọi API Upwork, giữ cookie Upwork hoặc thay đổi cách tiện ích lấy job. Định dạng nhận: POST tới đường dẫn bí mật, `Content-Type: application/json`, body có `event: "new_jobs"` và `jobs` gồm `id`, `title`, `url`, `description`, `budget`, `skills`, `client`, `postedAt`. Chống trùng theo `id`; gửi lại cùng ID không ghi đè các ghi chú hoặc trạng thái bạn đã chỉnh. ID job đã xóa vẫn được ghi nhớ để không tự xuất hiện lại ở lần gửi sau.

Bản GitHub có Webhook cắt mô tả còn 350 ký tự; cầu nối bản cài đọc toàn bộ mô tả đang có trong cache, tối đa 20.000 ký tự. Web hiển thị phần nhận được; mở job trên Upwork và bổ sung mô tả đầy đủ trước khi dùng AI. Thông tin quốc gia, chi tiêu, rating của khách hàng từ feed chưa đủ để tự tạo một khách hàng CRM có danh tính, nên bạn liên kết khách hàng khi đã xác định được họ.


## Proposal Studio và kho thư đã gửi

- **Canvas node:** kéo đầu node để đổi vị trí; kéo vùng trống để di chuyển canvas, dùng +/− hoặc Vừa khung để đổi mức phóng. Bấm cổng ● bên phải của nguồn rồi cổng ● bên trái của đích để nối. Chọn node để chỉnh nội dung trong bảng bên phải; có thể nối hoặc bỏ đầu vào tại đây.
- **Job → mẫu → thư nháp → AI đánh giá → thư cuối:** thông tin job và các mẫu đều nối vào thư nháp. Có thể thêm nhiều mẫu, thêm nhánh đánh giá, hoặc viết nội dung thủ công. AI chỉ sử dụng các node đầu vào trong luồng được nối; tối đa 30 node, 100 kết nối và không có vòng lặp.
- **Mẫu tham khảo:** chọn một mẫu đã lưu hoặc một thư trong kho đã gửi; thư có hợp đồng được gắn nhãn. Nhấn Lưu thành mẫu để dùng ở workspace khác. Thư thành công là dữ liệu tham khảo, không đảm bảo một mẫu sẽ luôn thắng job.
- **AI đánh giá:** điểm 0–100, bốn tiêu chí (phù hợp job, độ tin cậy, phạm vi / báo giá, bước tiếp theo), điểm mạnh, điểm yếu, đề xuất sửa. Đây là điểm đánh giá nội dung, không phải xác suất nhận hợp đồng. Nếu yêu cầu job, thư đầu vào, giá hoặc hồ sơ đổi, đánh giá được đánh dấu cần chấm lại. Node cuối có thể dùng nguyên thư nháp hoặc nhờ AI hoàn thiện theo phản hồi.
- **Lưu workspace:** nút Lưu giữ tên, vị trí node, các kết nối, nội dung và đánh giá trong SQLite. Những proposal cũ mở được trong workspace mới, giữ nội dung đã có. Có cảnh báo khi rời trang với thay đổi chưa lưu.
- **Thư đã gửi:** chỉ ghi nhận khi bạn xác nhận đã gửi trên Upwork. Nội dung, graph và thời điểm được lưu thành snapshot; sửa workspace hoặc cập nhật kết quả không sửa bản nguyên văn. Cùng workspace và cùng nội dung không tạo thêm snapshot trùng. Muốn ghi nhận một lần gửi khác, thay nội dung thư cuối.
- **Kết quả:** đang chờ, có hợp đồng, không có hợp đồng hoặc không phản hồi; thêm giá trị hợp đồng và ghi chú. Thống kê tỷ lệ thắng chỉ tính những thư đã chốt có / không có hợp đồng. Nút Dùng làm node mẫu đưa thư đã gửi vào workspace hiện tại và nối nó vào thư nháp.

## Thông báo trong web

Khi web đang mở, danh sách cập nhật mỗi 10 giây; job mới được đánh dấu chưa đọc trên tổng quan và danh sách công việc. Nhấn **Bật thông báo trình duyệt** để cho phép thông báo desktop nếu trình duyệt hỗ trợ. Khi đóng web, Slack/Telegram vẫn nhận được nếu máy chủ và tiện ích Chrome vẫn chạy; thông báo trình duyệt của web không chạy khi đóng trang. Nhắc liên hệ lại hiện nằm trong trang tổng quan, chưa tự gửi tới Slack/Telegram.

## Đăng nhập và triển khai

`FREELANCE_PASSWORD` bật đăng nhập riêng; phiên hết hạn sau 24 giờ hoặc khi khởi động lại máy chủ. Token webhook chỉ cho phép nhận job, không đọc hoặc sửa dữ liệu khác. Nhật ký máy chủ không ghi URL chứa token. Khi triển khai ngoài máy cá nhân, dùng reverse proxy HTTPS, bật mật khẩu và `FREELANCE_COOKIE_SECURE=1`, giữ cổng ứng dụng nội bộ và cấu hình reverse proxy không ghi token webhook trong access log. Máy chủ Python hiện phù hợp bản dùng riêng; chưa cung cấp hosting hoặc tên miền.

## Kiểm thử

```sh
python3 -m unittest discover -s tests -v
node --check public/app.js
node --check public/studio.js
```

Bộ kiểm thử backend kiểm tra đăng nhập, quyền webhook, chống trùng kể cả gửi đồng thời, nhập batch nguyên tử, CRUD và giữ metadata, hồ sơ AI, xử lý lỗi AI, hàng đợi và payload Slack/Telegram. Kiểm thử mới bao gồm graph không có vòng lặp, snapshot thư đã gửi giữ nguyên sau khi sửa workspace, chống ghi nhận trùng một nội dung, mẫu đầu vào AI và chấm điểm có cấu trúc. Các nhà cung cấp bên ngoài được mô phỏng; kết quả không chứng minh AI hoặc thông báo thật đã hoạt động.

Kiểm thử giao diện bổ sung (cần Playwright và `/usr/bin/chromium`):

```sh
python3 tests/browser_smoke.py
```

Kiểm thử này dùng dữ liệu tạm, kiểm tra đăng nhập, tạo khách hàng, hồ sơ, nhận job, luồng node viết nháp / chấm điểm, cảnh báo đánh giá cũ, thêm mẫu và nối node, kéo thả / lưu / tải lại, kho thư đã gửi, kết quả hợp đồng, tái sử dụng thư có hợp đồng, giao diện điện thoại và đăng xuất. Phản hồi AI được mô phỏng. Dữ liệu thật không bị thay đổi.

## Cơ hội công việc: quan tâm và đánh giá

Tab công việc dùng danh sách gọn, không có các ô thống kê tổng quan. Bấm **Quan tâm** để giữ job trong bộ lọc riêng tối đa 7 ngày; bấm lần nữa để bỏ quan tâm. Bấm lưu lại khi đang quan tâm không kéo dài hạn. Hết hạn tự bỏ dấu quan tâm, vẫn giữ job, thư và lịch sử. Hạn được kiểm tra bằng đồng hồ máy chủ khi đọc dữ liệu; web cập nhật mỗi 10 giây khi mở.

Di chuột lên job hoặc bấm **Đánh giá** (dùng được trên điện thoại) để xem tóm tắt tiếng Việt, nhận xét ngân sách, độ rõ của phạm vi và dấu hiệu rủi ro. Điểm gồm giá/phạm vi 25, mô tả rõ 20, ít dấu hiệu rủi ro 15, độ mới 15, cạnh tranh 10, lịch sử thuê 10, đánh giá khách 5. Các điểm thời gian được tính lại khi đọc danh sách, không gọi AI lại. Xanh cần ít nhất 80 điểm và các tiêu chí chính tốt; vàng cần cân nhắc/thiếu dữ liệu; đỏ khi giá quá thấp hoặc có dấu hiệu rủi ro rõ trong đánh giá. Điểm không phải xác nhận job an toàn hoặc xác suất có hợp đồng.

Toolkit cung cấp `proposalsTier`, thời điểm đăng/làm mới, sao và chi tiêu của khách. Chi tiêu dương là dấu hiệu đã dùng dịch vụ, không phải số lần thuê; số lần thuê chỉ dùng khi nguồn thực sự có `totalHires`. Dữ liệu thiếu được ghi rõ và không cộng điểm. Toolkit có thể cắt mô tả ở 350 ký tự; hãy bổ sung mô tả đầy đủ ở **Xem chi tiết → Bổ sung mô tả** để đánh giá lại. Ngày nhận webhook không được giả làm ngày đăng. Khi chưa cấu hình AI, job giữ màu vàng chưa đủ đánh giá, không tạo tóm tắt hay điểm AI giả. Lỗi AI được lưu để tránh tự gọi lặp tốn phí; bấm **Thử đánh giá lại** sau khi xử lý cấu hình/hạn mức.

Thẻ job có **Quan tâm**, **Đánh giá** và **Xem chi tiết**. Chi tiết là bảng đọc, không phải biểu mẫu chỉnh sửa: mô tả, kỹ năng, ngân sách, số người nộp, thời điểm nguồn và thông tin khách. Nút **Bổ sung mô tả** chỉ mở ô chỉnh nội dung khi cần; bấm hủy không ghi dữ liệu. Soạn thư tại tab Proposal Studio.

## Quốc gia, thời gian đăng và hoạt động khách

Thẻ công việc hiển thị quốc gia khách, thời gian đăng/làm mới tương đối và lần khách xem hoặc hoạt động gần nhất nếu có dữ liệu. Thời gian nguồn toolkit là `renewedOn ?? createdOn`, nên không coi đó chắc chắn là ngày đăng lần đầu; ngày nhận webhook không thay thế ngày đăng.

Webhook toolkit hiện tại **chưa chuyển hoạt động khách** dù dữ liệu chi tiết upstream có trường `clientActivity.lastBuyerActivity`. App không tự truy cập tài khoản Upwork để lấy trường này. Khi thiếu dữ liệu, giao diện ghi rõ chưa có. Bạn có thể vào **Xem chi tiết → Bổ sung lần khách xem job từ Upwork**, ghi nhận thời điểm “Last viewed by client” do Upwork hiển thị. Thời điểm xem được lưu riêng với thời điểm bạn ghi nhận, và luôn được ghi nguồn thủ công.

Nếu nguồn bổ sung dữ liệu trong tương lai, webhook hỗ trợ `clientActivity.lastViewedAt` hoặc `clientLastViewedAt` cho lần xem; `clientActivity.lastBuyerActivity` hoặc `lastActivityAt` cho hoạt động chung. Giá trị là ISO 8601 có múi giờ, không ở tương lai. Hoạt động chung không được gọi là lượt xem. Webhook lặp lại cùng ID cập nhật các mốc hoạt động, giữ mô tả bạn bổ sung và không gửi lại thông báo job mới. Lịch sử giữ tối đa 30 mốc khác nhau; đó là các mốc ứng dụng ghi nhận, không phải toàn bộ lịch sử truy cập của Upwork. Dữ liệu cũ hơn không làm lùi lần hoạt động mới nhất.

Khi dữ liệu hoạt động vừa được ghi nhận trong 30 phút và lần xem/hoạt động gần nhất đã cách ít nhất 5 giờ, job bị trừ 10 điểm ưu tiên, giữ nhóm vàng nếu chưa có lý do khác để đỏ. Không kết luận job bị bỏ hoặc là scam. Khi dữ liệu ghi nhận đã cũ hơn 30 phút, app nhắc cập nhật, không áp dụng phạt do thiếu hoạt động vì khách có thể đã quay lại. Những thay đổi này được tính theo thời gian khi đọc dữ liệu, không gọi AI lại.

## Mác đã gửi thư báo giá

Góc trên bên phải mỗi thẻ job có mác trắng khi chưa đánh dấu gửi thư. Tích vào chuyển xanh và ghi nhận thời điểm đánh dấu; tích lại để bỏ dấu. Trạng thái lưu trên máy, giữ qua tải lại và không hết hạn cùng dấu Quan tâm. Tab **Tổng quan** có số **Job đã gửi thư** và danh sách các job đã đánh dấu, mỗi job xuất hiện một lần. Có thể bỏ dấu ngay trong danh sách này.

Mác là xác nhận thủ công bạn đã gửi thư trên Upwork. Nó không gửi thư, không tạo bản thư giả trong kho **Thư đã gửi**, và không thay đổi nội dung thư đã lưu. Khi xác nhận **Tôi đã gửi → Lưu vào kho** trong Studio cho job được liên kết, app cũng bật mác job đó.

## Danh sách job gọn

Tab **Cơ hội công việc** chỉ nhận job tự động từ toolkit, không có nút nhập job thủ công. Tìm kiếm và bộ lọc nằm chung một thanh, bộ lọc có số lượng kết quả. Thẻ job dùng bố cục thống nhất: nội dung ở trái, ngân sách và thời điểm nguồn ở phải, thông tin hoạt động khách và các nút ở hàng dưới. Mô tả danh sách giới hạn hai dòng; bấm tên job hoặc **Xem chi tiết** để đọc toàn bộ phần mô tả đã nhận. Mác đã gửi thư, quan tâm 7 ngày, đánh giá AI và đồng bộ Tổng quan vẫn hoạt động. Trên điện thoại, giá/thời gian chuyển xuống một hàng riêng và bộ lọc vẫn hiện đầy đủ.

## Phễu lọc công việc

Bấm **Lọc** cạnh ô tìm kiếm để tích chọn thời gian đăng/làm mới, quốc gia khách, từ khóa, ngân sách, số proposal của job, sao của khách và trạng thái bạn đã/chưa gửi thư. Có thể bật nhiều nhóm cùng lúc: job phải đáp ứng tất cả nhóm đang bật; nhiều lựa chọn trong cùng nhóm được kết hợp theo “hoặc”. Từ khóa hỗ trợ khớp bất kỳ/tất cả cụm từ và loại trừ; tìm trong tiêu đề, mô tả và kỹ năng, không phân biệt dấu tiếng Việt hay chữ hoa.

Khoảng giá tính bằng USD, chọn riêng giá trọn gói hoặc theo giờ; toàn bộ khoảng giá của job phải nằm trong giới hạn đã nhập. Không so sánh giá theo giờ với giá trọn gói. Dữ liệu thiếu có lựa chọn riêng và không được tự xem là đáp ứng tiêu chí. Thời gian dùng mốc đăng/làm mới từ nguồn, không dùng ngày nhận webhook.

Bảng lọc hiển thị số kết quả trước khi áp dụng. **Hủy** giữ nguyên lựa chọn đã áp dụng; **Đặt lại** chỉ đặt lại bản nháp trong bảng. Sau khi áp dụng, có thể bỏ từng nhóm qua các nhãn dưới thanh tìm kiếm hoặc **Xóa điều kiện** để bỏ toàn bộ điều kiện nâng cao. Lựa chọn được lưu riêng trong trình duyệt và giữ qua tải lại trang; khi trình duyệt không cho lưu, bộ lọc vẫn hoạt động trong phiên hiện tại.

Kiểm thử logic lọc: `node tests/job_filters.test.js`. Kiểm thử trình duyệt bao gồm kết hợp điều kiện, xem trước kết quả, khoảng giá sai, lưu qua tải lại, hủy thay đổi và giao diện điện thoại.

Danh sách quốc gia có đầy đủ lựa chọn, hiển thị tên tiếng Việt và tiếng Anh, hỗ trợ tìm không dấu và cuộn để chọn nhiều nước. Tìm kiếm quốc gia không bỏ các nước đã tích. Tiêu đề và nút áp dụng luôn hiện khi cuộn phần điều kiện.

## Quản lý dự án và số liệu tháng/năm

Khi đánh dấu gửi thư ở thẻ job hoặc lưu thư đã gửi từ Studio, app tạo một bản theo dõi dự án cho job đó, không trùng khi gửi lại. Tab **Quản lý dự án** tách **Theo dõi thư đã gửi** theo tháng và **Kho hợp đồng** lưu tất cả job đã chốt, không giới hạn tháng. Bộ chọn tháng/năm dạng danh sách, nút tháng trước/sau và Tháng này dùng được trên máy tính và điện thoại. Danh sách theo dõi có nhóm Tất cả/Đang chờ và ô tích **Đã chốt hợp đồng**. Tích ghi ngày chốt; tích lại không đổi ngày. Bỏ tích đưa về đang chờ và bỏ ngày chốt. Kết quả đồng bộ với các thư lưu gắn cùng job; cập nhật kết quả trong kho thư cũng cập nhật dự án.

Số job gửi tính theo tháng gửi đầu tiên; hợp đồng tính theo tháng xác nhận chốt, múi giờ Asia/Bangkok (giờ Việt Nam). Danh sách theo dõi tháng chỉ gồm job gửi tháng đó. Kho hợp đồng luôn gồm tất cả job đã chốt, dù bạn đang chọn tháng nào. Ô đã chốt trong nhóm tháng tính các job gửi tháng đó đã có hợp đồng; Tổng quan vẫn thống kê hợp đồng theo ngày chốt. Số đang chờ tính trong nhóm job gửi tháng đó, không phải tổng lịch sử. Không lấy ngân sách job làm doanh thu và không suy đoán thư bị từ chối khi khách im lặng.

Sang tháng mới mặc định chuyển kỳ theo dõi, không xóa dữ liệu; có thể chọn lại tháng cũ. **Tổng quan** giữ tổng năm và bảng 12 tháng, chọn năm để xem lịch sử. Bỏ dấu gửi thư ở tab job không xóa bản theo dõi đã tạo hay kết quả hợp đồng. Job đã đánh dấu trước khi nâng cấp được đưa vào tab khi khởi động app. Dự án giữ tên/ngân sách/quốc gia lúc bắt đầu theo dõi dù job nguồn sau này thay đổi.

## Khách hàng: một bảng, ba nhóm

Tab **Khách hàng** có ba nhóm **Đang trao đổi**, **Hợp đồng đang mở**, **Lưu trữ**. Khách ở giai đoạn test vẫn thuộc Đang trao đổi; khách mất liên lạc nhưng còn hợp đồng thuộc Hợp đồng đang mở. Mỗi khách chỉ có một thẻ, chuyển nhóm trong hồ sơ mà không tạo khách mới. Các trạng thái cũ được hiển thị trong nhóm phù hợp, không xóa dữ liệu.

Thẻ ghi tình hình/milestone hiện tại, việc tiếp theo, ngày cần liên hệ và lần khách phản hồi gần nhất. Bấm **Vừa phản hồi** ghi ngày hôm nay theo giờ Việt Nam; chọn ngày khác trong hồ sơ. Số ngày tự tính, không tự kết luận Ghost. Hồ sơ gom ghi chú và các job/dự án/thư đã liên kết. Tìm kiếm và nút **Cần liên hệ** lọc các khách đến hạn, không nhắc khách lưu trữ.

**Email Upwork đã có tích hợp Gmail chỉ đọc**, cần cấu hình OAuth của riêng bạn. Vào **Khách hàng → Mở thư Upwork** để xem hộp tin nhắn. Trạng thái kết nối và nút chính nằm trên cùng; danh sách có bộ lọc Tất cả, Chưa đọc, Chờ liên kết. **Cài đặt kết nối** và **Nhập một thư** được thu gọn mặc định, chỉ mở khi bấm; thư đã liên kết chỉ hiện tên khách và nút Đổi khách. Chỉ truy vấn thông báo “sent you a message” từ `room_…@email.upwork.com` trong 30 ngày gần đây; không tải toàn bộ hộp thư, không gửi/xóa thư hay đổi trạng thái đã đọc trên Gmail. Quyền `gmail.readonly` Google cấp vẫn rộng hơn bộ lọc: có thể dùng hộp thư phụ chỉ nhận thông báo Upwork nếu muốn tách Gmail cá nhân.

Lần đầu chọn khách (hoặc tạo khách từ thư). App lưu liên kết theo mã phòng; các thông báo sau cùng phòng tự ghép, cập nhật ngày phản hồi và nhãn **Tin nhắn mới**; khách có thư chưa đọc được đưa lên đầu trong nhóm. Hộp thư app hiện 200 thư gần nhất. Không đoán theo tên, không tự xác nhận hợp đồng hay thay nhóm khách. Thông báo Gmail chưa xác minh được chữ ký DKIM Upwork phải ghép thủ công. Mở nội dung thư trong app xóa nhãn mới của thư đó, không thay trạng thái trên Gmail. Ngày phản hồi dùng ngày nhận email theo UTC+7, không lùi khi nhận thư cũ. Mẫu không trích được nội dung vẫn hiện thông báo và yêu cầu xem thư gốc; không bịa tin nhắn. Nhận/lọc/ghép thư không dùng AI; tự rút Việc tiếp theo là chức năng AI riêng, dùng token khi bật.

#### Cấu hình Google để nhận thư tự động

1. Mở [Google Cloud Console](https://console.cloud.google.com/), tạo/chọn project và bật **Gmail API** trong APIs & Services → Library.
2. Trong Google Auth Platform, thiết lập tên ứng dụng và Audience. Với ứng dụng cá nhân ở chế độ **Testing**, thêm địa chỉ Gmail muốn kết nối vào **Test users**.
3. Tạo OAuth Client loại **Web application**. Trong **Authorized redirect URIs**, thêm đúng URI được hiển thị trong app (mặc định `http://127.0.0.1:8000/api/mail/callback`). Không dùng API key Gemini hay Client loại Desktop.
4. Mở app bằng `127.0.0.1`, vào **Khách hàng → Mở thư Upwork → Cài đặt kết nối**, dán **Client ID** và **Client Secret**, lưu rồi bấm **Kết nối Google**. Chọn tài khoản và cấp quyền Gmail chỉ đọc.
5. Quay lại app, bấm **Đồng bộ ngay**. Khi server đang chạy, app tự kiểm tra mỗi 2 phút. Mỗi lượt tải tối đa hai trang (100 thông báo), lưu trang tiếp theo để lượt sau tiếp tục, tránh bỏ sót do các thư đã tải nằm trên đầu.

Thông tin OAuth và refresh token chỉ lưu trong `data/gmail-private.json` trên máy chủ (không trả token về trình duyệt; không nằm trong ZIP cập nhật). Giữ thư mục `data` riêng tư. **Ngắt kết nối** xóa token khỏi app và dừng đọc; thu hồi quyền hoàn toàn tại [quyền tài khoản Google](https://myaccount.google.com/connections). Google có thể làm token hết hạn sau 7 ngày khi OAuth còn ở Testing; bấm kết nối lại khi app báo hết phiên. `redirect_uri_mismatch` nghĩa là URI trong Google Cloud chưa khớp chính xác với URI app hiển thị. Kết nối Google thực tế cần Client ID/Secret của bạn; kiểm thử tự động chỉ mô phỏng phản hồi Google, không chứng nhận một tài khoản thật đã kết nối.

**Sau khi chép cập nhật:** dừng CMD bằng Ctrl + C, chạy lại start-windows.bat rồi Ctrl + F5 trên web. Máy chủ cũ đang chạy có thể đọc được giao diện mới nhưng chưa có route Gmail, khiến nút không mở được; bản mới hiện hướng dẫn khởi động lại nếu thiếu phần hộp thư.

#### Thử ngay bằng thư thật, chưa cần OAuth

Trong Gmail, mở thông báo Upwork → dấu **⋮ của thư** → **Tải thư xuống**. Trong app chọn **Nhập một thư → Chọn tệp thư .eml**, rồi liên kết khách. Tệp tối đa 700 KB. App chỉ đọc tệp bạn chọn, không có quyền vào Gmail; đây là nhập thủ công, không tự nhận thư mới. Nội dung nhập và thư Gmail lưu trong SQLite, chống nhập trùng theo ID thư. Ngắt Google không xóa lịch sử thư đã lưu.

## Tổng quan: biểu đồ và việc cần xử lý

Tổng quan không lặp danh sách job mới hay job đã gửi thư. Biểu đồ cột 12 tháng so sánh số job gửi thư (xanh) và hợp đồng chốt (vàng); bấm cột hoặc dùng bàn phím để chọn tháng. Nút mở dự án chuyển đến đúng tháng đang chọn. Chọn năm để xem lịch sử; không có dữ liệu hiển thị số 0, không nội suy. Số hợp đồng tính theo tháng/năm chốt, số thư theo lần gửi đầu tiên của job. Tỷ lệ chốt tính trên nhóm job gửi trong năm đã chọn, vì hợp đồng chốt trong năm có thể được gửi từ năm trước; đó là tỷ lệ hiện tại của nhóm, không phải dự báo.

**Việc cần làm** lấy từ lịch liên hệ đến hạn trong hồ sơ khách, loại trừ khách lưu trữ và việc đã đánh dấu hoàn thành. Bấm Hoàn thành giữ thông tin khách và lưu dấu cho lịch hẹn đó; sửa việc tiếp theo hoặc ngày hẹn sẽ bật lại theo dõi. **Cần quan tâm** hiển thị khách trong nhóm Hợp đồng đang mở có lần phản hồi ghi nhận cách ít nhất 7 ngày. Không suy đoán khách chưa có ngày phản hồi và không tự đánh dấu Ghost. Hoàn thành việc liên hệ không giả làm khách đã phản hồi. Các nhắc việc hiện trong Tổng quan; không tự gửi email/Slack/Telegram mới.

## Menu thu gọn

Trên máy tính, menu mặc định là dải biểu tượng rộng 76px; rê chuột hoặc đưa tiêu điểm bàn phím vào sẽ mở kèm nhãn. Bấm chọn tab vẫn giữ menu mở khi chuột còn trong menu. Rời menu tự thu gọn; nút trong menu cho phép giữ mở/thu lại. Menu mở phủ lên mép workspace, không làm thay đổi kích thước biểu đồ hoặc canvas. Trên điện thoại, nút menu mở ngăn điều hướng; chọn trang, bấm nền hoặc Escape để đóng. Người dùng bật giảm chuyển động sẽ không có hiệu ứng chuyển cảnh.

**Thư đã gửi** nằm trong Proposal Studio, có thanh chuyển giữa Không gian viết thư / Thư đã gửi và mục con trong menu mở rộng. **Hồ sơ & kết nối** ở cuối menu. Các trang và dữ liệu vẫn được giữ nguyên, chỉ gộp vị trí điều hướng.

## Tổng quan theo ưu tiên tuần

Bên cạnh biểu đồ là một ưu tiên chính và tối đa hai ưu tiên tiếp theo, dựa trên dữ liệu ghi nhận và sức tải bạn chọn. Tuần tính từ thứ Hai đến Chủ nhật theo giờ Việt Nam; phần Tuần trước dùng tuần đã kết thúc, không dùng 7 ngày trượt. Số khách đang trao đổi là trạng thái hiện tại, không giả làm lịch sử khách theo tuần.

Sức tải Chưa xác nhận / Còn thời gian tìm khách / Đang bận bàn giao được lưu theo tuần trong trình duyệt. Chỉ khi bạn xác nhận còn thời gian, có tối đa một khách đang trao đổi và tuần trước không có hợp đồng chốt, app gợi ý tìm thêm khách. Bận bàn giao không được nhắc tìm thêm bằng mọi giá. Việc đến hạn được ưu tiên, không lặp một khách vào nhiều gợi ý chính. Không có dữ liệu phản hồi theo từng thư thì không tính tỷ lệ phản hồi hoặc kết luận proposal kém. Gợi ý hiện dùng quy tắc, không phải nhận xét AI.

Bốn chỉ số năm, biểu đồ 12 tháng và ưu tiên tuần luôn hiện trên trang. Việc đến hạn và khách cần quan tâm được gộp thành một danh sách, không lặp cùng khách ở hai nhóm. Có bản xem báo cáo tháng trong web và tải Excel .xlsx. Báo cáo tách kết quả tháng khỏi trạng thái khách hiện tại; chưa có lịch sử chuyển nhóm để nhận xét khách theo tháng. **AI đánh giá báo cáo, lịch gửi cuối tháng và gửi Gmail chưa được triển khai**; giao diện ghi rõ Chưa tích hợp và không gửi email thật.

Kiểm thử gợi ý tuần: `node tests/focus.test.js`.

Trong Quản lý dự án, bấm tên job để mở/thu mô tả nhanh (tối đa 650 ký tự). Ưu tiên mô tả của job đang lưu; dự án mới giữ thêm bản mô tả dự phòng khi job nguồn bị xóa.

Menu Công việc gom hai tab con Tìm cơ hội và Theo dõi đã gửi. Tab Theo dõi đã gửi giữ nguyên chọn tháng, mô tả nhanh và Kho hợp đồng.

Các workspace dùng chung lề, cỡ tiêu đề và vị trí thanh tab; thanh cuộn giữ chỗ để tránh đổi bề rộng khi chuyển trang. Chuyển trang luôn về đầu; thông báo trạng thái nổi để không đẩy nội dung.

Khách hàng giữ ba nhóm, có trạng thái chọn ngay trên thẻ: khách mới/đang trao đổi, đang làm/chờ giao việc, đã đóng có/không có hợp đồng. Chọn trạng thái đóng chuyển khách sang Lưu trữ và ngừng nhắc liên hệ; có thể mở lại. Hồ sơ có đánh giá hợp tác tùy chọn: ổn/cần cân nhắc/nên tránh. Khách lưu trữ cũ chưa rõ hợp đồng giữ nhãn chưa phân loại.

Mỗi cột khách hàng có bộ lọc trạng thái riêng; bộ chọn trên thẻ chỉ thuộc nhóm hiện tại, nút Đóng chuyển sang Lưu trữ. Với Khách mới, ghi ngày gửi tin hỏi bằng nút Đã gửi tin hỏi hoặc trong hồ sơ. Từ đủ 14 ngày chưa có phản hồi vào/sau ngày hỏi, lần cập nhật dữ liệu tiếp theo sẽ lưu trữ khách (không xóa). Không áp dụng khi thiếu ngày hỏi, đã phản hồi hoặc đã chuyển sang đang trao đổi/hợp đồng.

Có thể kéo tay nắm ⠿ của thẻ khách sang cột khác trên máy tính. Nút Có hợp đồng chuyển khách đang trao đổi sang hợp đồng mở; Đóng ghi trạng thái trước đó; Mở lại khôi phục khách có hợp đồng về nhóm đang mở và trạng thái đang làm/chờ giao việc. Khách đóng không có hợp đồng mở lại về đang trao đổi; ngày hỏi cũ được bỏ để tránh tự lưu trữ lại ngay. Các nút là lựa chọn tương đương trên điện thoại; chỉ đổi hồ sơ CRM, không thay đổi hợp đồng Upwork hay kết quả dự án.

## Phân tích công việc

Trong Tổng quan có hai tab con Tổng quan / Phân tích. Trang chính chỉ thêm một nhận xét ngắn; trang Phân tích có kỳ 7, 30 hoặc 90 ngày, theo giờ Việt Nam:

- Nhịp job: biểu đồ từng ngày, bảng số liệu ngày và bảng màu thứ/giờ. Chọn riêng giờ đăng/làm mới do Upwork cung cấp hoặc giờ toolkit nhận. Có tùy chọn chỉ job xanh/vàng đã chấm. Không lấy giờ nhận thay cho giờ đăng còn thiếu; chỉ phản ánh job đã thu thập và còn trong kho.
- Các mốc chốt khách: nhóm job gửi lần đầu trong kỳ, không đếm lặp một job vì vừa có dự án vừa có thư lưu. Lượt xem của thư đã lưu có tổng riêng. Thư được xem / khách phản hồi chỉ tính thông tin đã ghi nhận; chưa biết để riêng. Job thắng chưa có mốc phản hồi vẫn được tính thắng, không tự bịa lượt xem.
- Mẫu thư: dùng đồ thị chụp lúc gửi, chỉ tính mẫu nối tới node thư cuối; bản lưu mới giữ cả ID thư cuối. Workspace sửa sau khi gửi không thay số liệu. Một thư có nhiều mẫu được tính vào từng mẫu, không cộng các hàng thành tổng thư. Tỷ lệ chốt chỉ tính kết quả đã kết thúc, loại trừ đang chờ; ít dữ liệu có nhãn cảnh báo.
- Trao đổi: từ các thao tác mới, hệ thống lưu ngày bắt đầu trao đổi và lần đầu ghi nhận hợp đồng; đóng/mở lại không đổi ngày chốt cũ. Hồ sơ cũ chưa có mốc không được đoán thành lịch sử theo kỳ. Khách đang trao đổi tách khỏi khách không chốt.
- Lý do không chốt là tùy chọn trên thẻ lưu trữ không có hợp đồng hoặc trong hồ sơ. Trong Thư đã gửi → Xem thư & kết quả có tùy chọn Chưa rõ / Chưa được xem / Đã xem / Khách phản hồi; không bắt nhập và không có kết nối tự lấy lượt xem Upwork. Cập nhật chỉ sửa thông tin theo dõi, không sửa nguyên văn thư hay đồ thị đã gửi.

Gợi ý tuần tới dùng quy tắc có số liệu và ngưỡng tối thiểu, tối đa ba nhận xét; chưa phải AI gọi nhà cung cấp. Nhắc tìm thêm khách chỉ khi sức tải tuần đã chọn còn thời gian. Không có thống kê Connects hoặc doanh thu. Dữ liệu mẫu trong demo là giả lập, tải lại sẽ đặt lại.

Kiểm tra bổ sung: `node tests/analytics.test.js` và `python -m unittest discover -s tests -p 'test_client_lifecycle.py'`. Browser smoke kiểm tra tab Phân tích, lưu quan sát thư, tải lại, kỳ phân tích và bố cục điện thoại.

Báo cáo tháng tải file Excel .xlsx thật (tạo trong trình duyệt, không gửi ra ngoài), gồm Tổng hợp / Công việc / Khách hàng / Thư đã gửi. Có tiêu đề xanh, dòng đầu cố định, bộ lọc và số liệu kiểu số; hỗ trợ tiếng Việt. Khách hàng là toàn bộ trạng thái hiện tại, được ghi rõ trong sheet Tổng hợp. Kiểm tra: `node tests/excel.test.js`.

### Giờ và ngày lễ Mỹ
Tổng quan có đồng hồ theo múi giờ khách (mặc định New York), tự cập nhật và tự tính giờ mùa hè. Múi giờ được nhớ trên trình duyệt. Lịch bao gồm các lễ liên bang, ngày nghỉ bù, Ngày của Mẹ, Ngày của Cha, Valentine, Halloween và Black Friday; thông báo dịp gần nhất và nhấn mạnh khi còn tối đa 7 ngày. Giải thích tiếng Việt giúp chuẩn bị lịch liên hệ; việc khách có nghỉ hay không tùy doanh nghiệp. Lịch tính trực tiếp, không cần kết nối dịch vụ ngoài. Kiểm tra quy tắc ngày lễ bằng `node tests/us_calendar.test.js`.

### Bố cục Tổng quan
Trang chia thành hai vùng: ưu tiên tuần và việc cần xử lý ở trên, kết quả năm và biểu đồ ở dưới. Giờ Mỹ, lịch lễ và số liệu tuần trước nằm ở cột bối cảnh riêng. Các ưu tiên bổ sung và nhận xét dữ liệu mở khi cần. Trên điện thoại, các khối chuyển thành một cột; chọn tháng, xem hồ sơ, hoàn thành nhiệm vụ và tải Excel vẫn dùng cùng dữ liệu.

### Proposal Studio · thao tác canvas
Bảng nội dung có thể mở bằng cách chọn node hoặc nút Nội dung node; đóng bảng để dùng toàn bộ chiều rộng canvas. Kéo nền để di chuyển, Ctrl/Cmd + lăn chuột để zoom theo con trỏ, hoặc dùng nút +/− và Vừa khung. Có thể kéo cổng ra sang cổng vào để nối, hoặc bấm hai cổng lần lượt; các quy tắc chống vòng lặp và kiểm tra loại node vẫn áp dụng. Xếp luồng sắp node theo kết nối từ trái sang phải, không thay đổi nội dung hay kết nối. Bản đồ nhỏ giúp đi đến node. Nút Mở rộng mở rộng workspace, Escape thu gọn. Chọn node bằng Tab và Enter; khi canvas có focus, dùng +/− để zoom và 0 để vừa khung. Nhấn Lưu workspace để giữ vị trí mới.

Node có nút × để xóa trực tiếp; các đường nối liên quan được gỡ cùng node. Bấm đường nối để bỏ nối trực tiếp; dấu × hiện khi rê chuột lên đường nối và luôn hiện trên thiết bị cảm ứng. Để đổi đích, bỏ nối cũ rồi kéo cổng sang node mới. Chọn kiểu cong, thẳng hay gấp khúc ở thanh canvas. Hoàn tác khôi phục lần xóa node/bỏ nối gần nhất trong workspace hiện tại. Có thể lưu workspace trống và thêm node lại sau; kiểu đường nối cũng được lưu. Kiểm tra quy tắc workspace trống và mức zoom bằng `python -m unittest discover -s tests -p test_workspace_editing.py`.

### Viết thư từ một cơ hội công việc
Trong chi tiết job, nhấn **Viết thư cho job này**. Studio mở workspace liên kết với job, đưa mô tả và ngân sách vào node Thông tin công việc và nối sẵn vào luồng thư nháp → đánh giá → thư cuối. Quay lại cùng job giữ nguyên bản đang viết; nếu đã lưu, ứng dụng mở lại workspace đó. Chuyển sang job khác khi workspace có thay đổi chưa lưu sẽ hỏi để tránh mất nội dung. Nội dung node đã chỉnh không bị ghi đè tự động khi job nguồn thay đổi. Nhấn Lưu workspace để lưu bản mới; mở workspace không đánh dấu đã gửi thư.

### Kho mẫu trong Proposal Studio
Nút Kho thư mở bảng kho bên cạnh workspace. Node kho có hai chế độ: AI tự chắt lọc (mặc định) đọc mọi thư được cho phép, hoặc Tôi chọn mẫu chỉ đọc những thư đã tích. Thư đến từ kho đã gửi và mẫu ngoài; có tìm kiếm, lọc nguồn, ghim ưu tiên, thêm mẫu mới. Không giới hạn kho ở 10 và không dừng phân tích ở 8 thư: backend đọc toàn bộ nguồn được chọn theo nhóm có giới hạn kích thước, rồi tổng hợp kết quả các nhóm trước khi viết nháp. Có thể chắt lọc cách mở đầu, giải pháp và câu hỏi từ nhiều mẫu; kinh nghiệm, danh tính và giá dùng hồ sơ thật của bạn. Chỉ node kho nối vào luồng viết mới được dùng. Một nút Chắt lọc & viết nháp chạy cả hai bước; phần kết quả chắt lọc và nguồn AI chọn được lưu cùng node viết. Chế độ thủ công cần ít nhất một mẫu; thư được chọn đã bị xóa thì không tự tìm thư khác để thay thế. Lỗi AI không thay nội dung bản nháp hiện tại. Để chạy thật cần khóa AI đã cấu hình; demo dùng phản hồi giả lập, không gọi nhà cung cấp. Kiểm tra đọc theo nhóm và tổng hợp bằng `python -m unittest discover -s tests -p test_reference_synthesis.py`.

## Job chưa xem trên tab Chrome

Biểu tượng tab là vòng tròn đỏ có số job chưa xem; trên 99 hiển thị `99+`, tiêu đề tab vẫn hiện tổng số chính xác. Khi không còn job chưa xem, biểu tượng trở về logo xanh. Dữ liệu đồng bộ mỗi 10 giây khi web đang mở. Vào mục **Công việc** đánh dấu cả lô job đã nhận là đã xem thông báo, lưu vào dữ liệu và giảm số ngay; job đến sau tiếp tục tăng số mới. Không cần mở từng job. Biểu tượng được phục vụ cùng nguồn nên không cần bật quyền thông báo hệ điều hành.


### Điểm khách và bộ lọc sao không dùng AI

Danh sách có bộ lọc Tất cả, 4–5 sao, 3 sao, 1–2 sao và Chưa đủ dữ liệu; điểm cao được xếp trước. Điểm khách tổng hợp khác với sao Upwork: sao Upwork chiếm 45%, số lần thuê 25%, tỷ lệ thuê 20%, xác minh thanh toán 10%; chỉ tính các thành phần có dữ liệu. Cần ít nhất hai thành phần, trong đó có lịch sử hoặc tỷ lệ thuê. Thiếu dữ liệu không tự cho 1 sao. Số lần thuê quy đổi 0/1/5/20/50 thành mức 1/2/3/4/5; tỷ lệ thuê 0/20/40/60/80% thành mức 1/2/3/4/5. Nếu nguồn cung cấp số job đăng và số lần thuê phù hợp, có thể tính tỷ lệ; nếu không, ghi rõ thiếu tỷ lệ thuê. Webhook nhận `client.hireRate` theo phần trăm 0–100 hoặc `client.totalJobsPosted`. Ngân sách dùng bộ lọc riêng, không quyết định chất lượng khách.

Rê chuột không mở bảng đánh giá. Trong khung **Phân tích công việc**, bấm **Phân tích bằng AI** mới gọi API cho job chưa có kết quả; đánh giá thành công được lưu trong SQLite, mở lại chỉ đọc cache. Chế độ tự chấm cũ bị tắt. Điểm sao không dùng token và không phải bảo đảm an toàn hay khả năng nhận hợp đồng.


### Khung chi tiết công việc và AI

Danh sách chỉ có nút **Phân tích công việc**, mở khung có nền sau tối nhẹ. Nút **Phân tích bằng AI** nằm trên cùng; phần kết quả thu gọn mặc định và chỉ sổ xuống khi bấm. Mở khung không gọi API; bấm nút AI mới xử lý job chưa có cache. Kết quả đã lưu được dùng lại khi mở phần AI, không gọi API lần nữa. Mô tả và thông tin khách nằm trong hai thẻ riêng, hoạt động khách được thu gọn. Có thể đóng bằng Escape, nút Đóng hoặc bấm ngoài khung; thanh Quan tâm, Viết thư và Upwork luôn ở dưới.

### Giữ kết nối qua lần đóng/mở ứng dụng

Windows dùng thư mục cố định `%LOCALAPPDATA%\FreelanceDesk\data`, nên giải nén bản cập nhật ở thư mục khác không tạo bộ cấu hình mới. Khi chạy lần đầu trên bản này, nếu nơi lưu cố định chưa có dữ liệu, app sao chép data cũ cạnh mã nguồn (SQLite bằng backup API, gồm khóa AI/kênh/Gmail và token webhook), giữ nguyên bản gốc và không ghi đè nơi lưu đã có dữ liệu. Để lấy đúng dữ liệu cũ, lần cập nhật đầu hãy chép bản mới vào đúng thư mục app đang dùng rồi chạy lại. Thư mục tường minh qua `FREELANCE_DATA_DIR` luôn được ưu tiên; đường dẫn tương đối tính từ thư mục mã nguồn, không từ CMD.

Xem nơi đang lưu tại **Hồ sơ & kết nối → Dữ liệu & kết nối đã lưu**. Các ô khóa/token không hiện lại giá trị cũ vì là ô nhập mới; nhìn trạng thái Đã cấu hình để biết khóa vẫn còn. Lưu lại cùng Client ID/Secret Google không xóa refresh token. Đóng CMD dừng server nhưng không xóa cấu hình; phải chạy app để web/worker hoạt động. Google Testing có thể làm phiên Gmail hết hạn sau 7 ngày; đây là hết phiên của Google, không phải mất dữ liệu khi đóng trình duyệt. Không gộp hoặc ghi đè hai data khác nhau nếu chưa xác định bản cần dùng.

### Chọn ổ/thư mục lưu dữ liệu trên Windows

Dừng CMD của app, mở **choose-data-windows.bat**, rồi chọn ổ hoặc thư mục cha. App tạo thư mục con **FreelanceDeskData** tại nơi đó (chọn D:\ thì lưu D:\FreelanceDeskData). Công cụ sao chép dữ liệu hiện có bằng SQLite backup, đóng mọi kết nối trước khi chuyển thư mục để tránh WinError 5, giữ bản gốc. Nếu đích đã có dữ liệu, công cụ hỏi có dùng bộ đó không; không gộp hay ghi đè. Sau khi chọn, mở **start-windows.bat** để chạy app; configure-windows.bat chỉ chỉnh khóa, không khởi động web.

Lựa chọn lưu trong `.storage-location.json` cạnh app và `storage-location.json` ở AppData nếu có quyền ghi. Biến FREELANCE_DATA_DIR vẫn ưu tiên hơn lựa chọn. Nếu AppData bị chặn nhưng dữ liệu cũ còn, app tiếp tục dùng data cũ để không làm bản cài hiện tại ngừng chạy. Cửa sổ Tk cần kiểm tra trên Windows; kiểm thử cloud xác minh logic chọn, sao chép, giữ bản gốc và đóng kết nối trước đổi tên.

### Chạy nền Windows, không giữ cửa sổ CMD

Dừng bản đang chạy bằng Ctrl+C một lần, rồi mở **start-background-windows.bat**. File này mở web và thoát cửa sổ chạy; server hoạt động trong tiến trình riêng không có console trên Windows. Bấm lại sẽ mở cùng server, không tạo thêm bản. Đóng tab/trình duyệt không dừng server; **stop-background-windows.bat** dừng đúng server chạy nền bằng token riêng, không taskkill mọi tiến trình Python. Mật khẩu web vẫn có hiệu lực.

Server vẫn cần máy bật/thức; sau khởi động lại máy phải mở file start-background lần nữa (chưa đăng ký tự chạy cùng Windows). Toolkit vẫn cần Chrome/extension hoạt động để thu thập job. Muốn cập nhật mã hoặc đổi nơi lưu, chạy file stop-background trước. Log nằm trong background-server.log ở thư mục dữ liệu; desktop-server.json là token điều khiển riêng, không chia sẻ hoặc đóng gói. Kiểm thử cloud đã xác minh child process sống sau launcher, reuse, auth, từ chối token sai và dừng giữ dữ liệu; cờ CREATE_NO_WINDOW thực tế cần xác minh trên Windows.

### Gỡ ứng dụng và dữ liệu

Mở **uninstall-windows.bat** trong thư mục app đã cập nhật. Cửa sổ gỡ hiện danh sách tệp: mã app, SQLite, khóa/token, log và vị trí lưu đã nhận diện (gồm data cũ nếu còn). Chỉ khi nhập **XOA** và bấm **Gỡ và xóa dữ liệu** công cụ mới thực hiện. Nó dừng phiên nền bằng token đúng; nếu app còn chạy trong CMD thì yêu cầu Ctrl+C trước và chưa xóa gì. Không dùng rmtree, không kill tất cả Python, không đụng file ngoài danh sách; folder có tài liệu riêng sẽ còn.

Xóa dữ liệu không có khôi phục qua công cụ này. Chỉ gỡ các bản/thư mục nhận diện trên máy đang dùng; ZIP đã tải, các bản sao lưu hoặc bản app khác ngoài danh sách không bị xóa tự động. Quyền OAuth Gmail cần thu hồi tại https://myaccount.google.com/connections và extension cần gỡ trong chrome://extensions. Công cụ không thực hiện tác vụ tài khoản từ xa. GUI Tk cần thử trên Windows; tests chỉ chạy xóa trong thư mục tạm giả lập.

### Thư đã nhận nhưng chưa hiện khách trên bảng

Kết nối Gmail chỉ nhận thư. Trong hộp thư, chọn khách đã có hoặc **+ Tạo khách…**, rồi bấm **Lưu liên kết**. Khách mới hiện trong Đang trao đổi; trạng thái hợp đồng không tự đổi. Tạo và ghép được ghi trong một giao dịch SQLite, lặp lại không tạo khách trùng cùng cuộc trò chuyện. Bản hiện tại dùng UTC+7 trực tiếp, không phụ thuộc tzdata thường thiếu ở Python Windows; lỗi cũ có thể làm POST tạo khách/ghép thư bị ngắt và browser báo Failed to fetch.

### Tự biết việc tiếp theo từ tin nhắn khách

Theo yêu cầu người dùng, **Tự rút việc tiếp theo từ tin nhắn bằng AI** bật mặc định trong hộp thư, có thể tắt bằng checkbox. Cần khóa AI đã lưu; đọc tin nhắn để hiểu việc cần làm có tính token của nhà cung cấp. Phần nhận/ghép email vẫn không dùng AI. Mail đã liên kết được xử lý theo khách, gom tối đa 8 tin gần đây (mỗi tin tối đa 2.000 ký tự), gồm ngữ cảnh dự án và việc hiện tại. Khi thêm tin mới, worker cập nhật thẻ khách; không cần bấm phân tích từng thư. Đây là tự động hiểu tin nhắn, **không bật lại tự chấm job**.

Kết quả lưu SQLite theo nội dung tin; mở trang, đánh dấu đọc hoặc khởi động lại không tự gọi lại phần đã hoàn tất. Một khách được xử lý mỗi lượt worker, không gọi dồn tất cả khách. Tin cảm ơn không tự xóa việc chưa giải quyết. Không thay nhóm/trạng thái hợp đồng hoặc tự gửi tin. Việc người dùng ghi được giữ; nếu đã có việc thủ công, AI hiện gợi ý riêng thay vì ghi đè. Không tự tạo deadline/date từ suy đoán. Khi thiếu khóa, app chờ khóa; khi API lỗi, giữ việc cũ, hiện lỗi và nút Thử lại, không lặp API liên tục cho cùng bộ tin.

App chạy nền và Gmail còn kết nối thì worker tự nhận thư và rút việc; màn hình cập nhật theo polling 10 giây. Thời gian còn phụ thuộc đồng bộ Gmail và API AI. Model chưa được kiểm chứng bằng tài khoản thật ở cloud; kiểm thử dùng provider giả lập.

### Báo thư chưa liên kết khách

Khi có thư Upwork chưa ghép được với khách, app hiển thị **Thư chờ liên kết** kèm số trên tiêu đề trang, dấu đếm ở mục Khách hàng và banner **Xử lý ngay** trong bảng khách. Bấm cảnh báo mở thẳng bộ lọc Chờ liên kết. Mở đọc thư không xóa cảnh báo; số giảm khi liên kết thành công. Nếu trình duyệt đã được cấp quyền, mỗi thư chờ mới phát thông báo, bấm thông báo mở danh sách xử lý. ID đã báo lưu ở trình duyệt để không báo lặp mỗi lần refresh; cảnh báo số vẫn tồn tại đến khi xử lý.

Thông báo trình duyệt cần trang app đang mở; khi đóng tab, thư vẫn lưu và cảnh báo hiện lần mở sau, không cam kết desktop toast khi không có trang chạy. Nhận/ghép thông báo không dùng AI. Tính năng này cảnh báo mọi thư chưa ghép (gồm khách mới/chưa xác định), không có nghĩa app đã tự ghép mọi khách theo tên.

### Tab báo cả job và tin nhắn cần xử lý

Tiêu đề Chrome hiển thị riêng, ví dụ **(3 job · 2 tin) Freelance Desk**. Favicon tròn đỏ đếm tổng 5, trên 99 hiện 99+. Tin cần xử lý là thư chưa đọc **hoặc** chưa liên kết; thư ở cả hai trạng thái chỉ tính một lần. Đọc thư đã ghép làm giảm số tin, nhưng đọc thư chưa ghép chưa đủ để xóa cảnh báo. Vào mục Công việc chỉ xóa thông báo job, không xóa tin nhắn.

Trên trang có nút **Tin chưa đọc** mở đúng bộ lọc Chưa đọc, bên cạnh **Thư chờ liên kết**. Dấu đếm Khách hàng tính tổng tin cần xử lý. Cơ chế đếm không dùng AI/token; worker rút việc vẫn theo thiết lập riêng.

### Hợp đồng đang mở nhưng cần tạm dừng

Trong thẻ khách ở **Hợp đồng đang mở**, chọn **Tạm dừng**. Ô lý do xuất hiện: khách im lặng/chưa phản hồi, chưa có việc mới, chờ tài liệu, chờ thanh toán, khách tạm hoãn, tôi tạm dừng hoặc lý do khác; ghi chú tùy chọn và bấm **Lưu lý do**. Thẻ vẫn ở nhóm hợp đồng mở, có ngày bắt đầu tạm dừng; bộ lọc trạng thái có Tạm dừng. Chọn Đang làm/Chờ khách giao việc để tiếp tục. Ngày tạm dừng và lý do được giữ; nhận email không tự bật lại trạng thái.

App không tự kết luận Ghost hoặc đóng hợp đồng do im lặng. Khách đã tạm dừng không bị tự đẩy vào danh sách ưu tiên chỉ vì 7 ngày không phản hồi; ngày hẹn liên hệ do bạn đặt vẫn được nhắc. Các trường này không dùng AI/token. Bản này cũng sửa cache AI có gợi ý hợp lệ nhưng ô Việc tiếp theo trống: dùng kết quả đã lưu, không gọi API thêm, không sửa ô đã ghi thủ công.


## Dấu trạng thái khách và hạn test — 12/10/2026
- Dấu màu kèm nhãn: hợp đồng working xanh, waiting vàng, paused đỏ. Đây là trạng thái người dùng chọn, không suy đoán ghost từ email.
- Nhóm trao đổi thêm chatting (chưa rõ nhu cầu), testing (đang test), negotiating (thương lượng); discussing cũ vẫn giữ dữ liệu nhưng không còn gộp với test.
- clientTestSentDate chỉ được ghi khi người dùng xác nhận ngày gửi test. Chỉ talk/testing mới tự lưu trữ sau 14 ngày nếu lastReplyDate chưa có hoặc trước ngày gửi. Phản hồi cùng ngày hoặc sau ngày gửi bảo vệ khỏi lưu trữ; ngày không hợp lệ không suy đoán im lặng.
- Quy tắc khách mới/clientInquiryDate trước đây giữ nguyên. Hợp đồng active không bị tự lưu trữ. Mở lại trao đổi xóa hạn cũ để không bị lưu trữ lại ngay.
- Máy chủ kiểm tra mỗi 60 giây khi chạy nền, và khi tải danh sách. Nếu máy/app tắt, kiểm tra lại khi mở. Không gọi AI/token cho màu và quy tắc hạn test.
- Kiểm tra: 100 Python tests, Node focus test, Chromium client_signals_smoke và client_pause_smoke đều PASS. Dữ liệu tạm; không gọi nhà cung cấp thật. Windows cần người dùng kiểm tra sau cập nhật.


## Thẻ khách thu gọn — 12/10/2026
- Mặc định đóng phần chi tiết bằng details/summary; hiện tên, màu + nhãn, tin mới, lần phản hồi, hạn test và một dòng việc tiếp theo.
- Bấm hoặc Enter/Space mở từng thẻ. Trạng thái mở giữ trong phiên qua refresh/poll; nhập ghi chú vẫn giữ draft. Kéo thẻ bằng nút ⠿.
- Phần trạng thái, lý do tạm dừng, test, hồ sơ và thao tác nằm bên trong. Không thay đổi backend hoặc quy tắc lưu trữ/kết nối.
- Tham khảo hướng bố cục Kanban/progressive disclosure. Pinterest và Dribbble bị proxy chặn 403; không tuyên bố đã đọc mẫu trực tiếp.
- Chromium: client_compact_smoke PASS (mặc định đóng, bàn phím, mở độc lập, refresh, light/dark, mobile); client_pause_smoke và client_signals_smoke PASS.


### Lý do tạm dừng thu gọn
Lý do + ghi chú tùy chọn được gom trong details/summary riêng, mặc định đóng. Lưu thành công xóa draft, đóng mục và đưa focus về tiêu đề; lỗi lưu giữ nguyên nội dung để thử lại. Bấm mở lại chỉnh sửa. Trạng thái mở giữ qua refresh trong phiên. Chromium pause/compact/signals smoke đều PASS, bao gồm tự đóng sau lưu và nội dung còn nguyên khi mở lại. Không thay đổi backend/dữ liệu.


## App Windows local — 12/10/2026
- desktop_app.py dùng pywebview/Edge Chromium + pystray. Đóng X ẩn cửa sổ, menu khay Mở ứng dụng/Thoát hoàn toàn. Mutex theo thư mục dữ liệu hạn chế mở trùng. Dùng desktop_background với private token để giữ máy chủ local và dừng đúng phiên, không kill mọi Python.
- Cài một lần: install-desktop-windows.bat → install_desktop.py tạo .desktop-venv, cài desktop-requirements.txt, tạo shortcut Desktop gọi trực tiếp pythonw/desktop_app.py (không CMD khi dùng hằng ngày). Python 3.10–3.13; Windows 10/11 + WebView2. Không có EXE độc lập đã build/ký; không tự khởi động cùng Windows.
- Giữ cùng data_directory/API/Gmail/Telegram/port và Toolkit. Native bridge chỉ mở URL local cố định ?openMail=1; Google đăng nhập trên trình duyệt ngoài vì embedded OAuth không phù hợp. Không truyền token/cookie qua bridge, không bỏ CSRF/OAuth state. Browser riêng có thể cần mật khẩu app.
- WebView profile trong data/desktop-webview, có marker sở hữu; uninstall chỉ liệt kê profile này khi có marker, không rmtree. Venv gỡ theo .desktop-installed-files.json của bộ cài; không chọn đường dẫn ngoài .desktop-venv hoặc traversal. Shortcut Desktop xóa thủ công. Không đóng gói venv/marker/cache/dữ liệu.
- 108 Python tests PASS; background_server_smoke, desktop_browser_smoke, Node focus PASS. Các wheel Windows cho Python 3.10/pywebview/pystray/Pillow/pythonnet đã tải được; proxy_tools đã build wheel. Lần resolve chỉ-binary ban đầu thất bại vì proxy_tools phát hành source; bộ cài pip bình thường cho phép build source, không tắt kiểm chứng TLS.
- GUI Windows, COM shortcut, WebView2/tray/mutex chưa thực thi trong cloud Linux; cần xác nhận trên Windows. Test lifecycle dùng mocks + backend child thật, dữ liệu tạm; không gọi AI/Gmail thật.


### Sửa khởi động desktop / chẩn đoán Windows
- Không còn gộp mọi lỗi thành “dừng CMD/kiểm tra WebView2”. Trước khởi động kiểm tra WebView2 registry ở HKCU/HKLM và cả 32/64-bit views, .NET release >=394802. Chặn renderer fallback MSHTML của pywebview 5.4.
- Bổ sung desktop_diagnostics.py + diagnose-desktop-windows.bat. desktop-diagnostic.txt chỉ có phiên bản/kiến trúc/thư viện/runtime/giai đoạn lỗi và exception đã che mẫu credential, không đọc config/private Gmail. Không đóng gói báo cáo thực tế.
- pythonw không có stdout/stderr thì cấp devnull trước import thư viện. Cleanup không destroy window khi chưa shown, tránh gọi GUI chưa khởi tạo. Mutex/storage exceptions cũng được báo.
- repair-webview2-windows.ps1 tải bootstrapper từ link Microsoft, bắt buộc Authenticode Valid + publisher Microsoft Corporation rồi mới chạy /silent /install; không bỏ TLS/chữ ký và không đổi execution policy. Bộ cài desktop tự gọi repair nếu thiếu runtime. .NET thiếu thì chỉ dẫn link Microsoft riêng.
- 114 Python tests PASS (lifecycle, thiếu runtime/.NET, registry views, che credential, cleanup init failure). Windows/PowerShell installation và registry thật chưa chạy trong Linux; chưa xác định nguyên nhân máy người dùng từ ảnh generic cũ. Nếu vẫn lỗi, lấy desktop-diagnostic.txt, không yêu cầu khóa API.


### Bộ cài chạy lại không ghi đè pythonw.exe
Ảnh Windows báo Errno13 khi venv ghi đè .desktop-venv/Scripts/pythonw.exe. install_desktop.ensure_environment kiểm tra Python/venv hiện tại bằng subprocess, dùng lại khi hợp lệ và không chạy python -m venv lần nữa. Nếu môi trường cài dở/hỏng thì giữ nguyên, báo hướng cài thư mục app mới thay vì xóa. PermissionError có thông báo riêng; bỏ quy mọi lỗi về Internet. Stop background chỉ dừng backend, người dùng phải đóng popup/Thoát hoàn toàn native app trước cập nhật. 119 Python tests PASS, gồm lần cài đầu, reuse không sửa pythonw, invalid/partial/symlink không ghi đè. Chưa mô phỏng khóa executable Windows thật trong cloud Linux.


### Sửa timeout dịch vụ local khi dùng Windows venv redirector
CPython 3.10 PC/launcher.c VENV_REDIRECT dùng CreateProcessW + wait cho runtime con; Popen.pid của venv/pythonw có thể là PID redirector, không phải os.getpid() của server. startup cũ gọi alive(item) với PID redirector nên không bao giờ nhận ready dù HTTP đã hoạt động.
- Bootstrap mới gọi /api/desktop/status bằng token random riêng; chỉ nhận ok=True và PID integer dương, lưu actual pid + launcherPid. alive/stop của phiên đã lưu vẫn bắt buộc token + PID thực khớp. Không kill arbitrary Python.
- Ép PYTHONUTF8 cho backend child để log Windows ổn định. Không tăng timeout để che lỗi.
- 124 Python tests PASS; background_server_smoke PASS; desktop_redirector_smoke dùng wrapper + server thật PID khác nhau: ready/reuse/stop kết thúc cả hai, dữ liệu giữ nguyên. GUI Windows vẫn cần kiểm tra trên máy người dùng.
- Tham chiếu đọc được: https://raw.githubusercontent.com/python/cpython/3.10/PC/launcher.c và https://raw.githubusercontent.com/python/cpython/3.10/PCbuild/venvlauncher.vcxproj (VENV_REDIRECT).


## Tổng quan Hôm nay và Tuần này — 13/10/2026
- Thẻ Hôm nay/Tin nhắn khách nằm trước Trọng tâm tuần này: số tin đến hôm nay theo UTC+7, chưa đọc, chờ liên kết, việc đến hạn; tối đa 5 preview tin cần kiểm tra, kể cả tồn từ trước.
- /api/mail/summary bổ sung todayCount/day và previews giới hạn 180 ký tự mỗi tin; chỉ qua API đã xác thực, không trả token/room/private OAuth. attentionCount vẫn union unread/unlinked, không cộng trùng.
- Summary thay đổi (kể cả cùng số lượng) làm Tổng quan và Khách hàng refresh trong poll hiện tại. Preview không tự đánh dấu đã đọc. UpworkMail.open(filter,messageId) mở đúng tin khi người dùng bấm; đọc pending không xóa chờ liên kết.
- Không gọi AI/Gmail thêm để tạo thẻ này, không thay stage/group hay ưu tiên tuần/lịch sử thống kê.
- 126 Python tests PASS; Node focus PASS; overview_mail_smoke Chromium PASS: ngày/tuần, live unlinked refresh, direct open/read, pending sau đọc, filter và mobile. Có screenshot light/dark bằng fixture, không dùng dữ liệu thật.


## Tổng quan ưu tiên tuần + việc AI gọn — 13/10/2026 (bố cục hiện tại)
- Theo yêu cầu sửa: Trọng tâm tuần ở đầu, bỏ khung preview tin lớn. Công việc hôm nay dùng các dòng AI action đã lưu + lịch đến hạn. Chờ liên kết/chờ AI chỉ là strip nhỏ dẫn vào hộp thư.
- Không bịa deadline hoặc gán followup=hôm nay từ văn bản AI. Hàng AI là gợi ý để chọn làm hôm nay; chưa có ngày thật ghi Chưa gán hạn. Placeholder/decision none không tạo việc giả, nhưng việc AI cũ thật vẫn giữ nếu thư xã giao chưa giải quyết nó.
- mailTaskSignature giữ qua keep/none; update mới tạo identity từ context signature. Đã làm lưu completedMailTaskSignature, không xóa lịch sử/nextAction thủ công. Thanks keep không mở lại task đã xong; yêu cầu update mới có thể hiện lại cùng nội dung. Nếu lịch hẹn và AI task khác nội dung cùng khách, vẫn giữ riêng.
- AI worker cached results backfill signature/source-id không gọi nhà cung cấp lại. states API thêm signature, chỉ là hash nội dung để nhận diện task, không phải token quản lý. Không sửa group/stage theo email.
- 127 Python tests PASS; mail_actions subset 12 PASS sau sửa metadata; overview_actions_smoke và overview_mail_smoke PASS (weekly-first, task completion/reload/thanks/new request, pending strip, no auto-read/no unlinked fake task/mobile), Node focus PASS. Mock provider/dữ liệu tạm, không dùng khóa thật.
