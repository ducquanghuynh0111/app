# Tác vụ

- [x] T037 Lưu chi tiết các hóa đơn đã thanh toán theo bàn và khu trong báo cáo sau ca, gồm cả món ngoài danh mục kho.
- [x] T038 Cho Thống kê chuyển giữa bàn đang mở và bàn đã đóng theo ngày; tạo báo cáo khi ngày chưa có báo cáo.
- [x] T039 Ghi chú từng hóa đơn, giữ ghi chú khi tính lại báo cáo cùng ngày.
- [x] T040 Kiểm thử bàn có nhiều lượt và chi tiết món đã đóng.
- [x] T041 Hiện giờ phát sinh hóa đơn cạnh số bàn và ô ghi chú của mỗi lượt, giữ đúng nhãn nguồn dữ liệu CUKCUK.

- [x] T034 Đổi lưới khu thành ba cột, cho bàn phân bố đều và bỏ cuộn ngang trong vùng khu.
- [x] T035 Mở chi tiết từng bàn bằng hộp thoại tên món, số lượng và trạng thái thiếu order.
- [x] T036 Tách các chỉ số thuốc cấp/trả/order/chênh lệch thành từng dòng.
- [x] T032 Chuyển nút Thống kê của từng thẻ khu sang mục riêng có bộ chọn khu; chỉ tải order khi bấm xem.
- [x] T033 Hiển thị kết quả theo danh sách nhóm và hàng, giữ quy đổi bia và thuốc.

- [x] T030 Thêm nút trừ và API sửa số gói đã lấy, không cho âm và giữ nhật ký.
- [x] T031 Bố trí khu và dòng thuốc không xô lệch hoặc lấp chữ; bản cập nhật T034 dùng ba khu một hàng.

- [x] T025 Chuyển thuốc cấp/trả/còn, số order và hóa đơn cần xác minh vào từng thẻ khu; gỡ khối sau ca riêng.
- [x] T026 Chia mặt hàng sau ca trong thẻ khu theo Bia, Rượu, Nước, Đồ ăn kèm và Thuốc; kiểm thử hiển thị khu riêng.
- [x] T027 Thêm nút + 1 gói cho hai loại thuốc trong từng khu và API tăng số đã lấy có ghi nhật ký.
- [x] T028 Cảnh báo đỏ theo order bàn đang mở tại lần tải gần nhất, thêm nút cập nhật order thủ công.
- [x] T029 Cho nhập số gói trả kho theo khu, tính chênh lệch đã lấy − trả kho − bán từ hóa đơn sau ca và tô đỏ nếu khác 0.

- [x] T021 Chuẩn hóa Nước theo thùng và Thuốc theo cây khi CUKCUK trả đơn vị đóng gói.
- [x] T022 Bổ sung danh sách loại Nước và Thuốc kèm quy cách vào API rà soát khu.
- [x] T023 Đổi Bia, Nước, Thuốc thành ba mục màu riêng, bấm xem chi tiết, mặc định thu gọn.
- [x] T024 Kiểm thử số theo loại và quy đổi trong giao diện mẫu cùng phép chiếu order.

- [x] T018 Sửa dữ liệu mẫu bàn 16 thành 2 lon Tiger và 2 lon Heineken; cộng với bàn 1 thành 1 thùng 2 lon Tiger, 2 lon Heineken.
- [x] T019 Truyền quy cách thùng theo mã bia vào rà soát khu, cộng và hiển thị bia riêng từng loại trong Thống kê.
- [x] T020 Kiểm thử hiển thị thống kê bia bằng dữ liệu mẫu và kiểm tra cú pháp JavaScript.

- [x] T013 Viết yêu cầu và kế hoạch đối chiếu sau ca theo tồn trước cộng nhập trong ngày.
- [x] T014 Đọc hóa đơn CUKCUK khi quản lý bấm tính, quy đổi bia/thuốc và lưu báo cáo theo khu.
- [x] T015 Đối chiếu kho toàn quán và hiển thị trạng thái chưa đủ dữ liệu khi thiếu mốc kiểm hoặc quy cách.
- [x] T016 Thêm vùng nhập thuốc cấp, trả, còn theo khu và ghi chú xác minh bàn thiếu order.
- [x] T017 Thử các phép tính quan trọng, kiểm tra cú pháp giao diện và chạy bộ kiểm thử hiện có.

- [x] T001 Tạo bảng dữ liệu và hàm tính toán thuần cho khu, phân công, cảnh báo và lần kiểm.
- [x] T002 Thêm API quản lý khu, bàn và phân công với kiểm tra dữ liệu/phân quyền.
- [x] T003 Thêm API ghi lần kiểm thực tế, đối chiếu CUKCUK và lưu kết quả xác minh.
- [x] T004 Tạo giao diện cấu hình và rà soát; bàn chưa có cấu hình vẫn hiển thị rõ.
- [x] T005 Kiểm thử các ca nghiệp vụ và chạy kiểm tra cú pháp/giao diện.
- [x] T006 Đổi màn hình thành thẻ khu tên nhân viên, thêm và sửa số bàn ngay trên thẻ.
- [x] T007 Chuẩn hóa nhãn bàn dạng số; tô đỏ bàn đang mở thiếu bia hoặc món kèm.
- [x] T008 Cộng số bia, nước, bánh tráng, đậu phộng và thuốc theo order của bàn trong từng khu.
- [x] T009 Đổi mỗi bàn thành một hàng có thể xổ đúng năm số lượng order; tên nhân viên mở phần sửa riêng.
- [x] T010 Sắp xếp số bàn theo số tăng dần trong khu và ở danh sách chưa gán.
- [x] T011 Quy đổi bia order theo thùng/két sang lon/chai bằng quy cách mặt hàng; hiện tên loại bia và số lượng cơ sở tại bàn.
- [x] T012 Thêm chế độ xem năm bàn mẫu trong hai khu; không lưu dữ liệu mẫu và có nút trở về dữ liệu thật.
