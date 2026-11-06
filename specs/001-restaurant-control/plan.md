# Kế hoạch triển khai

## Bổ sung: cài đặt máy mới và điều hướng gọn

1. Tạo `schema.sql` từ cơ sở dữ liệu rỗng do ứng dụng khởi tạo; kiểm tra không có lệnh ghi dữ liệu.
2. `caidat.py` nhập schema vào SQLite mới, không ghi đè DB cũ, rồi chạy web bằng Python hiện có. Không cài MySQL hoặc nhập dữ liệu máy cũ.
3. Giữ các tab chưa hoàn thiện ở trạng thái vô hiệu hóa với tên ngắn; thanh tab tự xuống dòng trên màn hình hẹp.

## Tóm tắt

Xây ứng dụng web nội bộ một chi nhánh để đối soát ca, ghi sổ kho và theo dõi nhân viên. CUKCUK vẫn là nguồn order; ứng dụng nhận số liệu tổng kết thủ công và CSV chuẩn hóa. Chênh lệch được hiển thị như ngoại lệ cần xác minh.

## Công nghệ

- Python 3.11, thư viện chuẩn http.server, sqlite3, decimal, hashlib.
- Giao diện HTML/CSS/JavaScript thuần, dùng trên điện thoại và máy tính.
- SQLite một file cho bản thử nghiệm; giao dịch ghi và ràng buộc ở máy chủ.
- Chạy mặc định trên 127.0.0.1; nhiều thiết bị cần máy chủ nội bộ và HTTPS qua reverse proxy.

## Cấu trúc

- app.py: HTTP API, xác thực, phân quyền, SQLite, nghiệp vụ.
- static/: giao diện và JavaScript.
- tests/: kiểm tra phép đối soát, kho, quyền và nhập CSV.
- data/: cơ sở dữ liệu vận hành, không đưa vào Git.
- specs/001-restaurant-control/: đặc tả, kế hoạch, tác vụ, hướng dẫn.

## Giai đoạn

1. Nền tảng: DB, tài khoản quản trị, đăng nhập, vai trò, nhật ký.
2. Đối soát ca: mở ca, số liệu CUKCUK, thu chi, tiền đếm, khóa ca, dashboard.
3. Kho: danh mục, nhập/xuất, kiểm kê, chênh lệch, duyệt điều chỉnh, cảnh báo.
4. Nhân viên: phân ca, chấm công, đi muộn, ghi sự cố order.
5. CSV và báo cáo: mẫu CSV chuẩn hóa, chống trùng, xuất báo cáo, kiểm thử.
6. Sau khi có mẫu xuất CUKCUK: ánh xạ Bảng kê hóa đơn, doanh thu theo món và món chế biến/trả lại; chọn mức theo dõi bàn giao món cùng quản lý.

## Quyết định và giới hạn

- Chưa tích hợp API CUKCUK vì cần xác nhận quyền/API và mẫu dữ liệu của quán.
- CSV yêu cầu mẫu chuẩn hóa của ứng dụng; ánh xạ file xuất thực tế làm sau khi có mẫu.
- Không tự đánh giá hiệu suất hay quy lỗi cho nhân viên; chỉ cung cấp số liệu và trạng thái xác minh.
- Bản đầu dùng nội bộ, chưa tối ưu cho nhiều chi nhánh hay tuân thủ kế toán.

## Kiểm tra

- Tính đúng tiền mặt kỳ vọng và số chênh theo ca.
- Không cho chỉnh ca khóa hoặc duyệt tồn trái quyền.
- Nhập CSV lặp lại không nhân đôi giao dịch.
- Kiểm kê 0 và chênh lệch âm/dương được lưu đúng.
- Nhân viên chỉ thấy ca của mình; chấm ra trước chấm vào bị từ chối.
