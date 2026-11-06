# Lịch sử kiểm kê hàng bán trực tiếp

## Bổ sung: thu gọn theo nhóm

- Bên trong mỗi ngày, Bia, Rượu, Nước, Đồ ăn kèm và Thuốc là các phần có thể bấm để thu gọn hoặc mở chi tiết; mặc định thu gọn để báo cáo ngắn hơn.

## Mục tiêu

Trong tab Kho, mục 1, quản lý xem lại số liệu bia, rượu, nước, món ăn kèm và thuốc theo ngày kinh doanh. Màn “Bàn đang gọi hàng” được bỏ khỏi tab Kho vì đã có trong Khu & rà soát.

## Tình huống sử dụng

1. Mục “Thống kê theo ngày” đóng sẵn; bấm tiêu đề mới thấy bộ lọc và danh sách ngày.
2. Chọn ngày, tuần hoặc tháng: mỗi ngày là một mục đóng; bấm ngày để xem các nhóm, rồi bấm nhóm để xem từng mặt hàng.
3. Với mỗi mặt hàng, thấy tồn cuối hôm trước, nhập hôm nay, số đã bán từ CUKCUK, tồn cuối thực tế và chênh lệch.
4. Ngày chưa đủ dữ liệu đồng bộ, thiếu đơn vị/quy cách hoặc thiếu mốc kiểm không được hiển thị chênh lệch như một kết luận.
5. Trong chi tiết từng ngày, mặt hàng được chia thành các phần Bia, Rượu, Nước, Đồ ăn kèm và Thuốc, có tiêu đề riêng để không phải đọc một bảng dài lẫn nhiều loại.

## Quy tắc

- Tuần bắt đầu thứ Hai; tháng là tháng lịch của ngày được chọn. Tất cả ngày trong kỳ đều có mục riêng để không che giấu ngày thiếu dữ liệu.
- Ngày kinh doanh theo giờ cắt hiện có, nên hóa đơn sau nửa đêm trước giờ cắt thuộc ngày trước.
- Số bán chỉ lấy từ hóa đơn đã thanh toán. Ưu tiên báo cáo sau ca đã lưu; nếu chưa có, dùng hóa đơn đã đồng bộ đủ và đơn vị của từng dòng hóa đơn để quy về đơn vị kho.
- Dữ liệu hóa đơn cũ chưa lưu đơn vị phải hiện “-” cho số bán và chênh lệch của hàng liên quan; đồng bộ lại kỳ đó sẽ bổ sung đơn vị.
- Chênh lệch = tồn cuối thực tế − (tồn cuối hôm trước + nhập hôm nay + hàng trả về kho − hỏng/tặng − số bán). Chỉ tính khi các thành phần và độ bao phủ hóa đơn đủ.
- Bộ lọc đọc dữ liệu cục bộ, không tự gọi CUKCUK và không tạo lịch quét.
- Chỉ vai trò đang được xem tab Kho mới xem được lịch sử; màn nhập kho hiện tại giữ quyền như cũ.

## Tiêu chí nghiệm thu

- Mở tab Kho không còn gọi API lấy bàn đang mở do khối trùng lặp đã bỏ.
- Mọi ngày đều đóng mặc định, kể cả khi lọc đúng một ngày; mục thống kê lớn cũng đóng mặc định.
- Trong một ngày có nhiều loại hàng, mỗi loại nằm trong phần riêng và vẫn có đủ năm số của từng mặt hàng.
- Mặt hàng bán theo thùng/cây được quy đổi đúng khi đơn vị hóa đơn và quy cách có sẵn.
- Ngày thiếu đồng bộ hoặc đơn vị không hiện 0 bán như một số đã xác nhận và không kết luận chênh lệch.
