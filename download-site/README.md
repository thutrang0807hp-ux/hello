# Trang tải Freelance Desk

index.html là mẫu tiếng Việt; trước khi có EXE thật, trang hiển thị trạng thái chờ, không tạo nút tải giả.

Workflow Windows build và kiểm thử bộ cài, sau đó chạy:

`python scripts/prepare_download_site.py dist/installer/FreelanceDesk-Setup.exe dist/website`

Thư mục dist/website chứa index.html, bộ cài thật và mã SHA-256, dùng được với mọi máy chủ tĩnh. Workflow cũng xuất bản các tệp vào GitHub Release và thử triển khai GitHub Pages. Không đưa dữ liệu người dùng, token hoặc cấu hình riêng vào website.
