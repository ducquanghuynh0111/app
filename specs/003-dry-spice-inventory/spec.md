# Feature Specification: Kiểm kê đồ khô và gia vị

**Status**: Đang làm rõ yêu cầu
**Input**: Quy trình kho quán nhậu; chủ quán muốn theo dõi nhập, tồn, hư hỏng mà không giảm định lượng gia vị làm ảnh hưởng chất lượng món.

## Clarifications

### Session 2026-11-05

- Q: Tab Đồ khô và gia vị chỉ kiểm nhập–tồn–hư hỏng hay áp định mức theo từng món? → A: Kiểm nhập, tồn, hư hỏng; không định mức theo món.
- Q: Kiểm tồn thực tế theo lịch nào? → A: Hằng tuần và kiểm đột xuất khi cần.
- Q: Có theo dõi giá mua không? → A: Mỗi tuần nhập đơn giá từng mặt hàng; tự so với lần nhập giá trước để thấy mặt hàng tăng hoặc giảm giá.
- Q: Nếu mua cùng mặt hàng theo quy cách khác nhau thì nhập giá thế nào? → A: Nhập giá và quy cách mua thực tế; phần mềm quy đổi về đơn vị chuẩn của mặt hàng trước khi so sánh.
- Q: Tuần không mua mặt hàng thì ghi giá thế nào? → A: Để trống giá mới; giữ giá mua gần nhất để tham khảo, không tự sao chép thành giao dịch mới.
- Q: Không có định mức món thì ước tính lượng dùng bằng cách nào, và có đề xuất nhập kỳ tới không? → A: Tính lượng dùng từ hai lần kiểm và số ngày giữa chúng để ra mức dùng bình quân/ngày; so giữa các kỳ và đề xuất lượng cần nhập kỳ tiếp theo.
- Q: Đề xuất nhập kỳ tới cần dự trữ bao nhiêu ngày? → A: Mặc định 7 ngày, quản lý có thể chỉnh riêng cho từng mặt hàng.
- Q: Đậu phộng bếp có dùng chung kho với đậu phộng bán kèm bàn (DAUPHONG/DAPH) không? → A: Không; là hai loại riêng và hai kho riêng.
- Q: Bột gà và Knorr có cùng một mặt hàng không? → A: Không; là hai mặt hàng khác nhau.
- Q: “Mắm rút” trong đơn bếp là tên đúng hay “mắm ruốc”? → A: Tên đúng là “mắm ruốc”.
- Q: “Bánh lề 20” là gì và tính theo đơn vị nào? → A: Bánh lề dùng cuốn ram, đơn vị gói; bánh tráng là hàng ăn kèm bàn, không gộp với bánh lề.
- Q: Ớt bột thường, tiêu, kỳ tử, táo tàu ghi số lẻ theo đơn vị nào? → A: Cả bốn đều tính theo kg.
- Q: Muối sống, đường phèn, bột chanh, bột gà, ớt bột Hàn Quốc, đậu phộng bếp tính theo đơn vị nào? → A: Cả sáu đều tính theo kg.
- Q: Tương cà, mắm, dầu hào và mắm ruốc tính theo đơn vị nào? → A: Tương cà, mắm và dầu hào theo chai; mắm ruốc theo hũ.
- Q: Bánh phồng tôm và cá ngừ tính theo đơn vị nào? → A: Cả hai theo hộp.
- Q: Sữa đặc tính theo đơn vị nào? → A: Lon.
- Q: Nước rửa chén, bao bóng và bao tay gỏi có nằm trong tab Đồ khô và gia vị không? → A: Không; chuyển sang tab Vật tư bếp riêng.
- Q: Ai nhập và sửa số liệu kho? → A: Chỉ quản lý hoặc chủ quán.
- Q: Ca kinh doanh của Kho theo mốc nào? → A: Dùng ca thu ngân hiện có; báo cáo tuần theo ngày bắt đầu ca.

## User Scenarios & Testing

### User Story 1 — Theo dõi đồ khô và gia vị (P1)

Quản lý hoặc chủ quán ghi số lượng nhận, số tồn thực tế và hàng hư hỏng của các mặt hàng cần theo dõi, rồi xem mức dùng bình quân/ngày giữa hai lần kiểm và so xu hướng giữa các kỳ. Kết quả không được dùng để ép bếp giảm gia vị hoặc thay đổi công thức món.

Kiểm tồn theo tuần và cho phép kiểm đột xuất khi cần.

**Acceptance Scenarios**:

1. **Given** mặt hàng có số nhận và số tồn được ghi, **When** quản lý xem báo cáo, **Then** thấy số lượng đã ghi và mức thay đổi; không hiển thị định mức tiêu hao theo món.
2. **Given** hàng bị hư hỏng, **When** nhân viên ghi nhận, **Then** báo cáo tách lượng hư hỏng khỏi lượng hao hụt chưa giải thích.
3. **Given** đã có đơn giá của lần nhập trước, **When** nhập giá tuần này, **Then** hiển thị mặt hàng tăng, giảm hay không đổi giá so với lần nhập trước.
4. **Given** hai lần kiểm có tồn và hàng nhập/hỏng trong khoảng giữa, **When** xem báo cáo, **Then** hiển thị lượng dùng ước tính và mức dùng/ngày theo số ngày thực tế giữa hai lần kiểm, kể cả kiểm đột xuất.
5. **Given** đã có mức dùng/ngày và tồn mới nhất, **When** xem kỳ tới, **Then** hiển thị lượng hàng đề xuất nhập theo 7 ngày mặc định hoặc số ngày riêng của mặt hàng.

### User Story 2 — Theo dõi biến động giá mua (P1)

Mỗi tuần, người phụ trách nhập giá và quy cách mua thực tế của từng mặt hàng đồ khô và gia vị. Phần mềm quy đổi về đơn vị chuẩn đã khai báo cho mặt hàng trước khi so sánh với lần nhập giá gần nhất.

**Acceptance Scenarios**:

1. **Given** mặt hàng chưa từng có giá, **When** nhập đơn giá lần đầu, **Then** lưu giá gốc và không gắn nhãn tăng hoặc giảm.
2. **Given** giá trước và giá mới, **When** lưu giá mới, **Then** hiển thị số tiền chênh lệch và chiều tăng hoặc giảm.
3. **Given** hai lần mua cùng mặt hàng theo hai quy cách khác nhau, **When** xem biến động giá, **Then** so sánh giá đã quy về cùng đơn vị chuẩn, đồng thời giữ giá và quy cách gốc của mỗi lần nhập.
4. **Given** một tuần không mua mặt hàng, **When** xem bảng giá tuần đó, **Then** không có giá mới; giá mua gần nhất chỉ hiển thị để tham khảo và không được tính là một lần cập nhật giá.

## Requirements

### Functional Requirements

- **FR-001**: Ghi nhận lượng nhập, tồn thực tế và hư hỏng cho đồ khô và gia vị được theo dõi.
- **FR-002**: Ước tính lượng đã dùng bằng tồn kỳ trước cộng hàng nhập trong khoảng, trừ hàng hư hỏng đã ghi và tồn kỳ này; chia cho số ngày thực tế giữa hai lần kiểm để có mức dùng/ngày. Hiển thị xu hướng giữa các kỳ, không tự kết luận thất thoát.
- **FR-003**: Không yêu cầu định mức sử dụng gia vị hoặc đồ khô theo từng món.
- **FR-004**: Cho kiểm tồn theo tuần và kiểm đột xuất khi cần.
- **FR-005**: Mỗi tuần cho nhập giá cùng quy cách mua thực tế; lưu lịch sử giá và quy cách gốc, quy đổi về đơn vị chuẩn rồi so với lần nhập giá trước của cùng mặt hàng.
- **FR-006**: Hiển thị giá tăng, giảm hoặc không đổi; lần nhập giá đầu tiên không có mốc so sánh.
- **FR-007**: Tuần không có lần mua thực tế thì để trống giá mới, chỉ hiển thị giá gần nhất với dấu hiệu rõ ràng là giá tham khảo.
- **FR-008**: Đề xuất lượng cần nhập kỳ tới từ mức dùng bình quân/ngày, số ngày cần dự trữ (mặc định 7, chỉnh được theo mặt hàng) và tồn mới nhất; hiển thị rõ các số đầu vào của phép tính.
- **FR-009**: Đậu phộng nguyên liệu bếp trong tab này là mặt hàng và kho riêng, không gộp tồn với món đậu phộng bán kèm bàn DAUPHONG/DAPH.
- **FR-010**: Bột gà và Knorr là hai mặt hàng kho riêng, có lịch sử tồn và giá riêng.
- **FR-011**: Bánh lề dùng cuốn ram là hàng bếp tính theo gói, tách biệt với bánh tráng bán kèm bàn.
- **FR-012**: Nước rửa chén, bao bóng loại 1 lít và bao tay gỏi không thuộc tab Đồ khô và gia vị; chúng được theo dõi tại tab Vật tư bếp riêng.
- **FR-013**: Chỉ quản lý hoặc chủ quán được nhập, sửa và xác nhận số liệu; mọi lần sửa số đã lưu có lịch sử người thực hiện và thời điểm.
- **FR-014**: Gắn các lần nhập và kiểm vào ca thu ngân hiện có; tổng hợp tuần theo ngày bắt đầu ca.

## Open Questions

- Người ghi, người xác nhận, cách sửa số đã chốt.
- Cách xác định ca/ngày và báo cáo xu hướng.
- Quy cách mua thường gặp và hệ số quy đổi khi giá mua theo đơn vị khác đơn vị kiểm tồn.


## Cập nhật quy tắc ngày 2026-11-05

Ngày kho do quản lý chọn khi nhập; không phụ thuộc giờ mở hoặc khóa ca thu ngân trong ứng dụng. Ô chưa nhập khác số 0. Quy tắc này thay thế mọi câu gắn ngày kho với ca thu ngân ở trên.

