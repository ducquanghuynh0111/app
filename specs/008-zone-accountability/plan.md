# Kế hoạch triển khai

## Bổ sung: hóa đơn bàn đã đóng

1. Trong bước chiếu hóa đơn sau ca, giữ từng hóa đơn đã thanh toán theo khu và bàn, kèm các dòng món cuối cùng, số lượng và đơn vị; không lưu dữ liệu khách hàng.
2. Cho mục Thống kê chọn bàn đang mở hoặc đã đóng theo ngày; dùng báo cáo đã lưu, tự tính khi chưa có và mọi bàn đã đóng.
3. Dùng khóa báo cáo và mã hóa đơn để lưu ghi chú từng lượt; sao chép ghi chú khi tính lại báo cáo trong ngày.
4. Kiểm thử bàn dùng nhiều lượt, món ngoài danh mục kho, hóa đơn chưa thanh toán và hiển thị ghi chú đúng lượt.
5. Hiện `RefDate` với nhãn giờ hóa đơn ở tiêu đề lượt và ô ghi chú; không diễn giải thành giờ đóng bàn chính xác vì API không cung cấp mốc đó.

## Bổ sung: thẻ khu ba cột và chi tiết bàn

1. Đổi lưới khu thành ba cột trên màn hình rộng và giảm theo kích thước cửa sổ; bàn trong khu dùng lưới ô tự phân bố đều.
2. Đổi ô bàn từ danh sách xổ xuống thành nút mở hộp thoại. Hộp thoại lấy dữ liệu order đã tải, liệt kê tên món và số lượng theo nhóm, giữ cảnh báo thiếu order.
3. Đổi phần thuốc sau ca thành danh sách chỉ số Đã lấy, Đã order, Đã trả kho và Chênh lệch, mỗi chỉ số một dòng.

## Bổ sung: mục Thống kê riêng

1. Gỡ nút Thống kê khỏi từng thẻ khu; thêm mục điều hướng riêng với bộ chọn khu.
2. Chỉ sau khi quản lý bấm xem mới tải lại order đang mở. Cộng bia, nước và nước ngọt, bánh tráng, đậu phộng, thuốc theo khu đã chọn.
3. Trình bày kết quả thành năm danh sách nhóm có thể mở chi tiết, giữ quy đổi thùng/cây và số lẻ.

## Bổ sung: bố cục khu và sửa thuốc

1. Thêm API giảm một gói, chặn dưới 0 và ghi nhật ký riêng cho lần sửa.
2. Bố trí thẻ khu thành ba cột trên màn rộng, tự giảm cột khi hẹp và giữ dòng thuốc gọn trong mỗi thẻ.

## Bổ sung: chi tiết Bia, Nước, Thuốc trong Thống kê khu

1. Chuẩn hóa order thùng nước và cây thuốc về đơn vị cơ sở trong cùng phép chiếu đang dùng cho bia.
2. Gắn mã, tên, nhóm và quy cách từng mặt hàng vào kết quả rà soát khu từ danh mục kho đang hoạt động.
3. Cộng số theo mã trong từng khu, rồi hiển thị các nhóm hàng có thể xổ; mặc định đóng khi bấm xem trong mục Thống kê.
4. Kiểm thử dữ liệu mẫu, quy đổi thùng/cây và trạng thái chưa biết quy cách.

## Bổ sung: đối chiếu sau ca

1. Dùng API hóa đơn kèm chi tiết CUKCUK theo ngày được chọn và ngày tiếp theo, lọc về ngày kinh doanh theo giờ cắt. Kiểm tra còn bàn đang mở trước khi tính ngày hiện tại.
2. Chiếu hóa đơn đã thanh toán sang hàng kho theo mã và đơn vị thực; đổi thùng bia và cây thuốc sang lon/chai/gói cơ sở. Giữ trạng thái chưa rõ khi quy cách hoặc mã chưa ghép.
3. Tính tồn dự kiến với số kiểm kho đang có, lưu báo cáo bất biến và ghi chú quản lý riêng. Tính thống kê theo khu từ hóa đơn của bàn được gán.
4. Thêm form thuốc cấp/trả/còn theo khu và hai ô cây/gói lẻ; đối chiếu sau khi quản lý nhập đủ.
5. Kiểm thử ngày qua 0 giờ, bàn dùng nhiều lần, hủy/chưa thanh toán, quy đổi đơn vị và số liệu thiếu.
6. Đặt phần thuốc cấp khu và kết quả sau ca vào từng thẻ khu; chia mặt hàng theo nhóm, bỏ khối kết quả toàn màn.
7. Đổi phần cấp thuốc sang hai nút tăng từng gói trong thẻ khu, lưu tăng ở máy chủ và đánh dấu thiếu order theo snapshot bàn mở. Cho nhập số gói trả kho sau ca và tính chênh lệch từ hóa đơn đã thanh toán.

- Dữ liệu SQLite: khu, bàn thuộc khu, phân công theo khoảng giờ, lần kiểm thực tế, dòng so sánh và kết quả xác minh.
- Backend: API quản lý khu/bàn/phân công có phân quyền; dùng lại luồng CUKCUK bàn đang mở để lấy snapshot khi kiểm.
- Tính toán: gom hai mã nước thành nhóm Nước; giữ bia, rượu, bánh tráng, đậu phộng, thuốc; chỉ so sánh nhóm được nhập số thực tế.
- Giao diện: thẻ khu theo tên nhân viên; mỗi bàn một hàng, bấm để xem số order và tên bia; nút Thống kê cộng các bàn đang mở.
- Dữ liệu mẫu: tạo snapshot tĩnh trong trình duyệt với hai khu và năm bàn; nút chuyển mẫu/thật không ghi cơ sở dữ liệu, không cho sửa dữ liệu mẫu.
- Kiểm thử: dữ liệu giả lập cho bàn thiếu bia, thiếu món kèm, đủ order, quy đổi bia thùng sang lon/chai, hai loại bia và thứ tự bàn theo số.
