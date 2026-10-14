## Bản cập nhật đã chốt 14/10/2026

- Nền trang trắng; Studio nền mint và nút màu theo node. Khả năng nhận thêm việc nằm dưới trọng tâm tuần; lịch Mỹ và analytics tăng tương phản.
- Tổng quan thống kê Tuần/Tháng, Năm riêng. Analytics thêm 6 tháng/1 năm theo lịch, biểu đồ gộp tháng cho kỳ dài.
- public/daily-tasks.js dùng dailyTasks trong hồ sơ khách, lưu vào SQLite qua API records. mail_actions.py giữ từng yêu cầu AI update theo signature, không dùng dữ liệu mẫu/localStorage để thay dữ liệu thật.
- Đầu việc có ngày giao, hạn sửa được, +1/+3/+7 từ ngày giao, màu theo hạn/tuổi. Chưa xong giữ lại; Đã xong chỉ hiện ngày hoàn thành hiện tại (00:00 UTC+7 làm trống danh sách, vẫn nhớ trạng thái để không hiện lại).
- Không có nút Qua ngày mai/Đặt lại mẫu trong app thật. daily-tasks.js đã thêm static route và HTML.
- Kiểm tra: 127 Python tests; analytics.test.js; overview_actions_smoke.py gồm lưu hạn/reload, hoàn thành/keep/new request, đổi ngày và mobile.
- Windows native/WebView2 vẫn cần xác nhận trên máy người dùng. Không đóng gói khóa, dữ liệu, venv hoặc profile.

# Bàn giao Freelance Desk — 12/10/2026

Đọc file này, AGENTS.md và DOC-TRUOC-KHI-SUA.md trước khi sửa. Đây là mã nguồn đầy đủ, không phụ thuộc tài khoản ChatGPT đã viết nó. Không cần ZIP app cũ để chạy mã trong gói.

## Trạng thái cần biết ngay

- App Windows local: cửa sổ pywebview/WebView2 + khay pystray; Python 3.10–3.13. Chưa có EXE độc lập đã build/ký. Không cần host. Đóng X ẩn vào khay; Thoát hoàn toàn mới dừng.
- Bộ cài: install-desktop-windows.bat. Shortcut Desktop gọi pythonw/desktop_app.py. open-desktop-windows.vbs là cách mở phụ. install_desktop.py dùng lại venv hợp lệ, không ghi đè pythonw.exe khi chạy lại.
- Sửa mới nhất: desktop_background.py không nhầm PID Windows venv redirector với PID server thật. Bootstrap chỉ nhận PID qua desktop/status đã xác thực token; alive/stop vẫn so actual PID. Có desktop_redirector_smoke.py tái hiện bằng hai tiến trình thật.
- Người dùng đã gặp Permission denied pythonw.exe và timeout dịch vụ local. Đã gửi bản sửa cả hai; CHƯA nhận được xác nhận cửa sổ Windows đã mở thành công sau bản cuối. Không tuyên bố Windows GUI đã kiểm thử từ Linux.
- Nếu lỗi tiếp: diagnose-desktop-windows.bat tạo desktop-diagnostic.txt (không đọc khóa). WebView2 có công cụ repair, bắt buộc chữ ký Microsoft hợp lệ. Không quy mọi lỗi về CMD/Internet, không kill mọi Python.

## Chạy ở đâu

**Windows:** đọc CAI-APP-DESKTOP.txt, dừng bản cũ hoàn toàn, giữ dữ liệu và .desktop-venv; chạy bộ cài một lần trong thư mục đã giải nén. Máy mới cần cài Python/WebView2 và tạo venv mới. Venv máy cũ không đóng gói để đem sang máy khác.

**Codex/Linux:** backend dùng stdlib + SQLite. Tại thư mục chứa server.py:

```sh
FREELANCE_DATA_DIR=/tmp/freelance-desk-test python -m unittest discover -s tests -p 'test_*.py' -q
python tests/desktop_redirector_smoke.py
python tests/background_server_smoke.py
node --test tests/focus.test.js
```

Để kiểm tra HTTP, đặt FREELANCE_DATA_DIR vào thư mục tạm và PORT chưa dùng rồi chạy server.py. GUI Windows không chạy trong cloud Linux. Smoke UI dùng Playwright và Chromium /usr/bin/chromium; đọc script trước, điều chỉnh executable phù hợp với môi trường. Không gọi nhà cung cấp thật để test.

## Các hành vi đã chốt

- Job: sao/lọc tính local; phân tích AI bấm thủ công, tiếng Việt, cache, gộp trong Phân tích công việc. Không hover gọi AI.
- Khách: thẻ thu gọn, mở từng thẻ; giữ trạng thái mở qua poll. Lý do tạm dừng và ghi chú cùng một mục mở xuống, lưu thành công tự đóng.
- Màu khách là trạng thái người dùng chọn, không đoán ý định tuyển/ghost. Active working/waiting/paused vẫn trong hợp đồng mở; không tự lưu trữ vì im lặng.
- Talk/testing chỉ tự lưu trữ sau 14 ngày từ clientTestSentDate rõ ràng và không có reply cùng ngày/sau ngày gửi. Giữ quy tắc new/clientInquiryDate cũ; mở lại xóa hạn cũ.
- Gmail lọc email Upwork bằng ứng dụng, quyền OAuth readonly vẫn rộng hơn bộ lọc. Ghép room đã biết hoặc người dùng chọn; không tự ghép chỉ dựa tên. Không đồng nhất tin nhắn với hợp đồng.
- AI rút Việc tiếp theo từ thư đã ghép có toggle và cache; người dùng đã cho phép. Không thay trạng thái/nhóm hoặc xóa việc thủ công vì thư cảm ơn.
- Native Gmail OAuth mở trình duyệt ngoài qua URL local cố định; giữ kiểm tra cookie/state, không nhúng Google trong WebView.
- Giữ thông báo job/mail riêng, clearing job không xóa pending mail.

## Dữ liệu và phát hành

- data_store.py là nguồn thống nhất; Windows mặc định LOCALAPPDATA/FreelanceDesk/data hoặc vị trí đã chọn. Không xóa/ghi đè dữ liệu để sửa lỗi.
- Gói này không chứa API key, token, Gmail session, dữ liệu khách, venv, WebView cache, log chẩn đoán hay Git credentials. Tài khoản Codex khác không cần biết khóa của người dùng để sửa.
- Cùng máy Windows: giữ thư mục dữ liệu, các kết nối đã lưu có thể dùng lại. Máy mới: dữ liệu/kết nối cần người dùng tự sao lưu/chuyển riêng, không tải lên chat hoặc Git công khai.
- scripts/package_handoff.py tạo gói nguồn có SHA256 từng file và quét private/token/nested ZIP. Manifest nhận diện chính xác mã đóng gói.
- Gói cập nhật runtime cần đủ module/public/installer/uninstall allowlist; giữ data và venv. Dừng app hoàn toàn trước chép đè.
- Toolkits build/source có trong downloads; không tự sửa extension ngoài yêu cầu. Bản preview cũ không phải nguồn chuẩn.

## Việc Codex tiếp theo cần làm

Tiếp tục yêu cầu người dùng dựa trên mã hiện tại, không viết lại từ đầu. Đọc HANDOFF-VALIDATION.txt để biết kiểm thử và giới hạn. Nếu người dùng chưa mở được desktop, lấy thông báo/báo cáo đã che dữ liệu để chẩn đoán cụ thể. Hoàn tất thay đổi, kiểm thử liên quan, cập nhật tài liệu và tạo gói để người dùng chép vào bản cũ.

Cập nhật 13/10/2026: Tổng quan có thẻ Hôm nay/Tin nhắn khách trước ưu tiên tuần; mail summary trả tối đa 5 preview đã xác thực, nút mở đúng thư, không auto-read preview. 126 Python tests + overview_mail_smoke PASS.

Bố cục hiện tại sau chỉnh 13/10: Trọng tâm tuần FIRST, phía dưới Công việc hôm nay là action AI đã lưu + lịch hẹn, strip nhỏ cho thư chưa ghép/AI chưa xong. Bỏ card mail preview lớn. Có completion signature giữ sau reload/thanks, update request mới hiện lại. 127 unit tests và hai overview smoke PASS.
