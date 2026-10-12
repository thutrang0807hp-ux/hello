"""Windows folder picker. Stop the app before switching storage."""
import os
import socket
from pathlib import Path
from data_store import choose_directory, ROOT


def main():
    try:
        with socket.create_connection(('127.0.0.1',int(os.environ.get('PORT','8000'))),timeout=.5):
            print('App/cổng đang chạy. Nhấn Ctrl+C trong CMD của app rồi mở lại file chọn nơi lưu.')
            return 1
    except OSError:pass
    if os.environ.get('FREELANCE_DATA_DIR'):
        print('Máy đang đặt FREELANCE_DATA_DIR. Xóa biến này hoặc chỉnh nó trước khi dùng vị trí đã chọn.')
        return 1
    root=None
    try:
        try:
            import tkinter as tk
            from tkinter import filedialog,messagebox
            root=tk.Tk();root.withdraw();root.attributes('-topmost',True)
            folder=filedialog.askdirectory(parent=root,title='Chọn ổ/thư mục: dữ liệu sẽ nằm trong FreelanceDeskData',mustexist=True)
        except Exception:
            folder=input('Nhập ổ/thư mục muốn lưu, ví dụ D:\\ (Enter để hủy): ').strip().strip('"')
        if not folder:return 0
        destination=Path(folder)/'FreelanceDeskData'
        if destination.exists() and any(destination.iterdir()):
            if root is not None:
                if not messagebox.askyesno('Dùng dữ liệu đã có?', 'Thư mục đích đã có dữ liệu. App sẽ dùng dữ liệu ở đó, không gộp/ghi đè dữ liệu cũ. Tiếp tục?',parent=root):return 0
            elif input('Thư mục đích đã có dữ liệu; dùng bộ này? Nhập YES để tiếp tục: ').strip()!='YES':return 0
        target=choose_directory(destination,root=ROOT)
        text='Đã chọn: '+str(target)+'\nDữ liệu gốc vẫn được giữ. Mở start-windows.bat để chạy app.'
        print(text)
        if root is not None:messagebox.showinfo('Đã lưu vị trí',text,parent=root)
        return 0
    except Exception as error:
        print('Chưa đổi được nơi lưu: '+str(error))
        if root is not None:messagebox.showerror('Chưa đổi được nơi lưu',str(error),parent=root)
        return 1
    finally:
        if root is not None:root.destroy()


if __name__=='__main__':raise SystemExit(main())
