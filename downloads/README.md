# Toolkit bản cài hiện tại + cầu nối Freelance Desk

Dùng [Toolkit-Installed-Build-Bridge.zip](Toolkit-Installed-Build-Bridge.zip) cho bản Chrome Web Store 1.6.0 người dùng đã gửi. Gói giữ mã lấy job của bản đó và thêm phần chuyển cache sang web trên máy bạn.

[Hướng dẫn Windows](../toolkit-bridge/INSTALL-WINDOWS.txt) · [Mã nguồn tương ứng](Toolkit-Installed-Build-Source.zip) · [Mã cầu nối và kiểm thử](../toolkit-bridge/README.md).

Các gói `Upwork-Toolkit-Webhook.zip` và `Upwork-Toolkit-Source.zip` dưới đây là bản build GitHub khác, có Mobile alerts sẵn; không cần cài chúng khi dùng cầu nối bản hiện tại.

---

UPWORK TOOLKIT KẾT NỐI FREELANCE DESK

Đây là bản build từ mã nguồn upstream, không phải bản cập nhật Chrome Web Store.
Mã nguồn gốc: https://github.com/neeilya/upwork-toolkit
Commit: e75003468d373353e69ff46c1c54cec02100ae41
Giấy phép GPL-3.0; mã nguồn tương ứng đi kèm dưới dạng ZIP riêng.

1. Giải nén Upwork-Toolkit-Webhook.zip vào thư mục cố định.
2. Mở chrome://extensions và TẮT bản Toolkit cũ (không cần xóa).
3. Bật Developer mode / Chế độ nhà phát triển.
4. Bấm Load unpacked / Tải tiện ích đã giải nén.
5. Chọn thư mục toolkit-webhook, bên trong phải có manifest.json.
6. Mở Extension options / Tùy chọn tiện ích của bản vừa cài.
7. Chọn Mobile alerts -> Webhook.
8. Mở Freelance Desk bằng start-windows.bat, vào Hồ sơ & kết nối, sao chép URL nhận job.
9. Dán vào Webhook URL, bấm Save và Allow khi Chrome hỏi quyền.
10. Bật Webhook và bấm Send test; kiểm tra job mẫu trong Freelance Desk.
11. Đăng nhập Upwork trên cùng Chrome; chọn lại feed và các cài đặt mong muốn.

Giữ cửa sổ chạy Freelance Desk và Chrome mở để nhận job.
Bản cài mới không tự chuyển cài đặt/lịch sử từ tiện ích cũ.
Không xóa hoặc di chuyển thư mục toolkit-webhook sau khi cài.
Nếu muốn quay lại, tắt bản mới và bật bản cũ.
Không chia sẻ URL webhook vì URL có mã bí mật.
Build thành công; việc nhận job Upwork thực tế cần kiểm tra trên máy của bạn.
