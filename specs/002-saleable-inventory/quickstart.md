# Hướng dẫn xác minh tính năng

## Chuẩn bị

1. Dùng cơ sở dữ liệu thử, không dùng dữ liệu bán thật.
2. Khởi động ứng dụng bằng `python app.py` và đăng nhập vai trò chủ quán hoặc quản lý.
3. Chạy `python -m unittest discover -s tests -q` và `node --check static/app.js`.

## Kịch bản bàn

1. Chuẩn bị một bàn mở có BATR, một bàn mở có DAUPHONG, một bàn mở có DAPH và một bàn mở không có hàng kèm.
2. Mở **Khu theo nhân viên** để xem bàn đang mở và tải dữ liệu CUKCUK. Hai mã đậu phộng đều làm bàn được tính là đã có đậu phộng; chi tiết giữ mã gốc.
3. Kiểm tra bàn không có bia màu đỏ dù có rượu/nước; bàn có bia nhưng thiếu hàng kèm màu cam; bàn đã đóng không xuất hiện.
4. Nếu danh mục CUKCUK chưa ánh xạ được mã, kiểm tra trạng thái “Chưa xác định”, không kết luận bàn thiếu.

## Kịch bản kiểm kê và đối chiếu

1. Chọn đầu ngày: chỉ thấy **Nhập hàng**, ô số mặc định 0; nhập số thùng và xác nhận.
2. Khi còn bàn mở, thử kiểm cuối ca và xác nhận bị chặn. Sau khi đóng hết bàn, chọn cuối ca: nhập số thùng nguyên và số chai/lon lẻ, rồi lưu số thực tế.
3. Nhấp một lần vào ô nền xanh để sửa, rời ô để lưu; bảng không đổi kích thước. Người không có quyền chỉ thấy số đọc.
4. Kiểm tra HUDA chai 20, Budweiser lon 28, rượu 12 chai/thùng và các quy cách còn trống là 24.
5. Mở chi tiết theo bàn; khi không có lịch sử hủy từng dòng, cột trả/hủy phải là “Chưa có dữ liệu”.
6. Với rượu 1 thùng và 3 chai lẻ, kiểm tra tồn quy đổi là 15 chai. Nếu hóa đơn ca chưa đồng bộ đủ, số kiểm vẫn lưu nhưng chênh lệch ở trạng thái chờ; sau khi đồng bộ đủ mới tính.
7. Với ca qua 0 giờ, kiểm tra số nhập, hóa đơn và số kiểm vẫn thuộc ca thu ngân bắt đầu trước 0 giờ. Vai trò ngoài chủ quán/quản lý không được nhập hoặc sửa số kho.
