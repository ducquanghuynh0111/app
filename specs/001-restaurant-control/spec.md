# Đặc tả: Kiểm soát vận hành quán nhậu

## Mục tiêu

- Trong giai đoạn dùng thử kho, ba tab Đối soát tiền, Nhân viên và Nhập CUKCUK bị vô hiệu hóa bằng kiểu hiển thị mờ, giữ tên ngắn để thanh tab tự xuống dòng thay vì cuộn ngang. Tài khoản nhân viên vẫn vào được tab Quy trình.
- Trên máy mới, một lệnh cài đặt tạo cơ sở dữ liệu SQLite trống từ tệp SQL chỉ chứa cấu trúc bảng, rồi chạy ứng dụng. Không đưa dữ liệu vận hành máy cũ vào bản cài và không ghi đè cơ sở dữ liệu đã có.
Ứng dụng nội bộ giúp chủ quán thấy chênh lệch giữa CUKCUK và thực tế theo ca, kiểm soát nhập xuất tồn tới bia, thuốc, nước chấm và gia vị, cùng theo dõi giờ làm và lỗi order. Ứng dụng bổ sung lớp kiểm soát cho CUKCUK, không tự sửa dữ liệu CUKCUK.

Quán có một chi nhánh, tám nhân viên phục vụ và năm nhân viên bếp. Phục vụ order trên điện thoại bằng CUKCUK; bếp nhận bill in; tiếp thực đọc bill và bưng món khi bếp hoàn tất. Quyền trong ứng dụng và bộ phận làm việc được lưu riêng.

## Vai trò

- Chủ quán/quản lý: xem toàn bộ dữ liệu, duyệt điều chỉnh, khóa ca.
- Thu ngân: nhập tổng kết ca, thu chi và số tiền đếm được.
- Bếp/kho: đề xuất mua, ghi nhập hàng và kiểm kê.
- Nhân viên: xem ca, chấm vào/ra, báo lỗi order.

## Quy trình đề xuất

1. Đầu ca: giao tiền đầu ca, kiểm đếm nhóm hàng dễ thất thoát, phân công nhân viên.
2. Trong ca: CUKCUK là nguồn order/bill; thu chi ngoài bill ghi vào sổ ca; hàng nhập có người nhận và người duyệt.
3. Cuối ca: nhập tổng kết CUKCUK, nhập tiền thực nhận, kiểm kê hàng trọng yếu, hệ thống tính chênh lệch.
4. Quản lý xử lý ngoại lệ rồi khóa ca; mọi chỉnh sửa có nhật ký.
5. Hằng tuần: xem xu hướng lệch tiền, lệch kho, sự cố; điều chỉnh định lượng và ngưỡng đặt hàng.

## User Scenarios & Testing

### US1 — Đối soát doanh thu theo ca (P1)

Thu ngân nhập doanh thu CUKCUK theo tiền mặt và chuyển khoản hoặc nhập CSV; nhập tiền thực nhận và các khoản thu chi. Tiền mặt kỳ vọng = tiền đầu ca + doanh thu tiền mặt + thu khác - chi tiền mặt - hoàn tiền. Hệ thống hiển thị chênh lệch với tiền đếm được và yêu cầu giải trình khi vượt ngưỡng.

**Tiêu chí chấp nhận:** cùng mã giao dịch CUKCUK không nhập hai lần; tiền lưu theo đồng nguyên; ca khóa không sửa được; quản lý xem được chứng từ và nhật ký điều chỉnh.

### US2 — Nhập hàng và kiểm kê toàn bộ vật tư (P1)

Danh mục gồm bia, thuốc, nguyên liệu, nước chấm, gia vị và nhóm khác. Mỗi hàng có đơn vị chuẩn, tồn tối thiểu và giá nhập gần nhất. Phiếu nhập, phiếu xuất/hao hụt và phiếu kiểm kê ghi người thực hiện, thời điểm, số lượng, lý do. Kiểm kê tạo chênh lệch chờ duyệt, không âm thầm ghi đè tồn.

**Tiêu chí chấp nhận:** lưu được số kiểm kê 0; số lượng không âm; cảnh báo dưới tồn tối thiểu; bia và thuốc có số nhập, số bán, số đếm và chênh lệch.

### US3 — Kiểm tra bán ra và thất thoát (P1)

Quản lý nhập hoặc tải số lượng bán theo mã hàng CUKCUK. Hàng bán trực tiếp như bia và thuốc được trừ tồn theo đơn vị. Món chế biến có thể khai báo định lượng ở giai đoạn sau; bản đầu cho phép xuất kho thủ công và gắn lý do. Chênh lệch bán/kiểm kê tạo ngoại lệ.

**Tiêu chí chấp nhận:** báo cáo phân biệt hao hụt, biếu, trả/hủy và thiếu chưa giải thích; không kết luận gian lận từ chênh lệch đơn lẻ.

### US4 — Ca làm, đi muộn và lỗi order (P2)

Quản lý tạo ca và giao nhân viên. Nhân viên chấm vào/ra; hệ thống so với giờ phân ca và dung sai cấu hình. Quản lý ghi lỗi order với mã bill, loại lỗi, người liên quan, giá trị và trạng thái xử lý. Báo cáo chỉ hiển thị chỉ số quan sát được, không tự động chấm điểm nhân viên.

**Tiêu chí chấp nhận:** không chấm ra trước chấm vào; chỉnh giờ cần duyệt và lý do; nhân viên chỉ xem dữ liệu của mình.

### US5 — Đối chiếu hóa đơn mẫu và bàn giao món (P2, cần làm rõ)

Hóa đơn thanh toán mẫu cho thấy số hóa đơn/order, bàn, nhân viên phục vụ, thu ngân, món, số lượng, đơn giá, thành tiền và tổng thanh toán. Hóa đơn không đủ để xác nhận phương thức thanh toán thực nhận hoặc trạng thái món đã bưng. Dùng Bảng kê hóa đơn và báo cáo món chế biến/trả lại của CUKCUK làm nguồn đối chiếu khi quán xác nhận có thể xuất dữ liệu. Trong bản đầu, ghi ngoại lệ theo mã bill thủ công; không yêu cầu bếp và tiếp thực nhập lại mọi món.

**Cần xác nhận:** quản lý muốn ghi sự cố ngoại lệ, xác nhận từng món qua mã bill, hay chỉ dùng báo cáo CUKCUK cuối ca.

## Yêu cầu chức năng

- FR1: Đăng nhập và phân quyền chủ/quản lý, thu ngân, kho/bếp, nhân viên.
- FR2: Danh mục hàng có mã duy nhất, nhóm, đơn vị, tồn tối thiểu, trạng thái.
- FR3: Phiếu nhập, xuất/hao hụt và kiểm kê có lịch sử; điều chỉnh tồn cần duyệt.
- FR4: Ca tiền có tiền đầu, doanh thu theo kênh, thu chi, tiền đếm và chênh lệch.
- FR5: Nhập CSV chuẩn hóa có xem trước, kiểm tra cột, báo lỗi dòng và chống trùng theo mã nguồn. Ánh xạ trực tiếp file xuất CUKCUK cần mẫu thực tế.
- FR6: Ca nhân viên, chấm công, ghi nhận đi muộn và sự cố order.
- FR7: Dashboard cho ca chưa khóa, lệch tiền, lệch tồn, hàng dưới ngưỡng.
- FR8: Nhật ký ai làm gì, khi nào, lý do cho thao tác quan trọng.
- FR9: Xuất báo cáo CSV và sao lưu cơ sở dữ liệu.

## Ràng buộc

- Tiền là số nguyên VND; số lượng là số thập phân theo đơn vị chuẩn.
- Có mã chi nhánh và mã ca dù bản đầu mặc định một chi nhánh.
- Phân quyền ở máy chủ, mật khẩu băm, phiên đăng nhập có hạn.
- Không lưu dữ liệu thật của khách hay nhân viên trong mã nguồn.
- Báo cáo vận hành không thay thế sổ kế toán hoặc chứng từ thuế.

## Kết quả đo được

- Mọi ca nhập đủ dữ liệu hiển thị chênh lệch tiền và người phụ trách.
- Mọi kiểm kê hàng trọng yếu hiển thị chênh lệch với tồn sổ.
- Mọi điều chỉnh tiền, tồn, giờ công có người thực hiện, thời điểm và lý do.
- Xuất được báo cáo cuối ca trong dưới một phút với dữ liệu cỡ một quán.

## Thông tin đã xác nhận

- Một chi nhánh, tám nhân viên phục vụ, năm nhân viên bếp.
- Phần mềm mới bổ sung bên cạnh CUKCUK. Order trên điện thoại trong CUKCUK; bếp nhận bill in và tiếp thực bưng món.
- Đã có ảnh hóa đơn mẫu để nhận diện trường dữ liệu; chưa có file báo cáo Excel/CSV hoặc dữ liệu phương thức thanh toán.

## Giả định cần xác nhận

- Bản đầu là ứng dụng web dùng trên điện thoại và máy tính, chạy nội bộ.
- CUKCUK tiếp tục xử lý order/thu ngân; ứng dụng nhận dữ liệu tổng kết hoặc CSV.
- Cần mẫu file xuất CUKCUK để hoàn thiện ánh xạ CSV.
- Chấm công bằng nút vào/ra, chưa có GPS, sinh trắc học hoặc máy chấm công.
