# Kế hoạch triển khai

- Chuyển từng nhóm mặt hàng trong chi tiết ngày thành phần đóng/mở độc lập, giữ bộ lọc và năm số liệu của mỗi dòng.

1. Bỏ khối bàn đang gọi hàng ở Kho và lời gọi API CUKCUK khi chỉ mở tab Kho. Giữ dịch vụ bàn cho Khu & rà soát.
2. Lưu đơn vị từng dòng hóa đơn CUKCUK khi đồng bộ, có migration cho cơ sở dữ liệu cũ.
3. Thêm API lịch sử ngày/tuần/tháng đọc kho và hóa đơn đã lưu, tính theo ngày kinh doanh, xử lý trạng thái thiếu dữ liệu.
4. Thêm bộ lọc và danh sách ngày có thể xổ; mục thống kê, từng ngày và từng nhóm đều đóng mặc định.
5. Kiểm thử khoảng ngày, đổi đơn vị, dữ liệu thiếu, quyền truy cập và giao diện.
6. Chia chi tiết từng ngày thành năm nhóm có tiêu đề và bảng riêng, bỏ cột nhóm lặp ở từng dòng.
