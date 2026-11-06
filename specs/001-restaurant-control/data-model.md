# Mô hình dữ liệu

| Bảng | Nội dung chính |
| --- | --- |
| users | tài khoản, vai trò quyền truy cập, bộ phận phục vụ/bếp/tiếp thực, mật khẩu băm, trạng thái |
| sessions | phiên đăng nhập ngẫu nhiên, hạn dùng |
| cash_shifts | giờ mở/khóa, người phụ trách, tiền đầu, doanh thu CUKCUK, tiền đếm, lý do lệch |
| cash_entries | thu/chi/hoàn tiền ngoài bill, số tiền, chứng từ, người tạo |
| items | mã hàng, tên, nhóm, đơn vị, tồn tối thiểu |
| stock_moves | nhập, bán, hao hụt, điều chỉnh; số lượng, lý do, người tạo |
| stock_counts | số sổ, số đếm, chênh lệch, trạng thái duyệt |
| work_shifts | người được phân, giờ bắt đầu/kết thúc, chấm vào/ra |
| order_incidents | mã bill, loại lỗi, mô tả, giá trị, trạng thái |
| sales_imports | mã nguồn duy nhất, ca, hàng, số lượng, doanh thu |
| audit_log | hành động, đối tượng, người thực hiện, thời điểm, lý do |

Tiền dùng INTEGER VND. Số lượng lưu dạng chuỗi thập phân chuẩn hóa để tránh sai số nhị phân. Điều chỉnh được ghi thêm, không cập nhật đè lịch sử nhập/xuất.
