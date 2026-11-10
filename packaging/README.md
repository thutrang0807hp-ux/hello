# Tạo bộ cài EXE Windows

Bản đóng gói dành cho Windows 10/11 x64, kèm Python trong ứng dụng. Người dùng không cần cài Python. WebView2 và .NET Framework 4.6.2+ vẫn là thành phần hệ thống bắt buộc.

## Build bằng GitHub Actions

Đưa các thay đổi này lên repo, mở **Actions → Build Windows EXE → Run workflow**. Khi tác vụ thành công, tải artifact **FreelanceDesk-Windows-x64**, giải nén và mở `FreelanceDesk-Setup.exe`. Workflow chỉ chạy khi chủ động bấm; không tự tạo GitHub Release.

Workflow build trên Windows và kiểm tra backend EXE thật: khởi động, tài nguyên web, xác thực dừng bằng token, khởi động lại và giữ dữ liệu. Đây chưa phải kiểm thử cửa sổ WebView2/khay hệ thống tương tác.

## Build trên máy Windows

Cài Python 3.12 x64 và Inno Setup 6, mở PowerShell tại thư mục repo:

```powershell
py -3.12 -m venv .build-venv
.\.build-venv\Scripts\python.exe -m pip install -r packaging/build-requirements.txt
.\.build-venv\Scripts\python.exe -m PyInstaller --noconfirm --clean packaging/FreelanceDesk.spec
.\.build-venv\Scripts\python.exe tests/frozen_backend_smoke.py dist/FreelanceDesk/FreelanceDesk.exe
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" packaging/installer.iss
```

Kết quả: `dist/installer/FreelanceDesk-Setup.exe`. Giữ nguyên toàn bộ thư mục `dist/FreelanceDesk` nếu dùng bản portable; không chép mỗi EXE ra ngoài thư mục này.

## Cài đặt, cập nhật và dữ liệu

Bộ cài không yêu cầu quyền quản trị, tạo shortcut Desktop và Start Menu. Trước khi cập nhật/gỡ cài đặt, chọn **Thoát hoàn toàn** ở khay hệ thống, dừng phiên nền của bản cũ và sao lưu dữ liệu. Bộ cài không xóa `%LOCALAPPDATA%\FreelanceDesk\data`, gồm SQLite/cấu hình/token. Lựa chọn thư mục dữ liệu đã lưu trong AppData tiếp tục được dùng. Nếu bản cũ chỉ có lựa chọn cạnh mã nguồn hoặc dùng FREELANCE_DATA_DIR, hãy giữ biến đó hoặc chọn lại đúng nơi trước khi chuyển sang EXE; không sao chép khóa vào bộ cài.

Nếu app báo thiếu WebView2, chạy `repair-webview2-windows.bat` trong thư mục cài (chỉ chấp nhận bootstrapper có chữ ký Microsoft hợp lệ), rồi mở lại. .NET thiếu thì cài từ Microsoft theo thông báo. Bộ cài không tự tải prerequisite. Shortcut chẩn đoán ghi `desktop-diagnostic.txt` trong thư mục dữ liệu. Các tích hợp AI/Gmail/Toolkit giữ cách cấu hình cũ.

Bộ cài hiện chưa ký mã Authenticode; chứng chỉ ký mã cần cấu hình riêng. Linux cloud chỉ kiểm chứng mã nguồn và backend theo entry point mới; chỉ báo EXE build thành công sau khi workflow Windows thành công. Kiểm tra thêm trên Windows: mở app không có Python, khay hệ thống, Thoát, mở lại, đăng nhập Google qua trình duyệt ngoài, cập nhật và gỡ mà vẫn giữ dữ liệu.

## Xuất bản trang tải và EXE

Push nhánh `codex/windows-download` hoặc chạy workflow thủ công sẽ build và kiểm tra backend của EXE trước và sau khi chạy bộ cài. Khi các bước này thành công, workflow tạo bản phát hành thử nghiệm có EXE, SHA-256 và ZIP website chứa chính EXE đó. Job Pages triển khai website, chỉ có nút tải khi EXE tồn tại và có header PE hợp lệ. Nếu Pages chưa bật hoặc bị chính sách repo chặn, bước triển khai có thể cần chủ repo bật GitHub Pages với nguồn GitHub Actions; bản phát hành EXE vẫn được giữ.

Không còn dùng liên kết tải tới đường dẫn workspace hay ZIP mã nguồn trên trang dành cho người dùng.
