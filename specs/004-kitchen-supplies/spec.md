# Feature Specification: Kho vật tư bếp

**Status**: Đang làm rõ yêu cầu
**Input**: Ba mặt hàng phi thực phẩm trong danh sách đặt của bếp được chuyển sang tab kho riêng.

## Clarifications

### Session 2026-11-05

- Q: Nước rửa chén, bao bóng và bao tay gỏi có nằm trong tab Đồ khô và gia vị không? → A: Không; theo dõi ở tab Vật tư bếp riêng.
- Q: Có thể dùng thời gian, số lượng nhập và khoảng cách giữa các lần nhập để gợi ý nhập vật tư không? → A: Có; ước tính sơ bộ mức dùng từ lịch sử nhập và đưa ra gợi ý nhập, hiển thị rõ đây là ước tính.
- Q: Cần kiểm tồn vật tư bếp ở mức nào để hiệu chỉnh dự báo? → A: Ghi tồn ban đầu; kiểm lại hằng tháng hoặc khi cần.
- Q: Có theo dõi giá mua vật tư bếp như tab Đồ khô và gia vị không? → A: Có; lưu giá và quy cách mua thực tế, quy đổi để so với lần mua trước của cùng mặt hàng.
- Q: Ai nhập và sửa số liệu kho? → A: Chỉ quản lý hoặc chủ quán.
- Q: Ca kinh doanh của Kho theo mốc nào? → A: Dùng ca thu ngân hiện có; không tạo ca kho riêng.

## User Scenarios & Testing

### User Story 1 — Xem vật tư bếp riêng (P1)

Người quản lý xem vật tư phi thực phẩm tại tab riêng, không lẫn với nguyên liệu chế biến hoặc hàng bán kèm bàn.

**Acceptance Scenarios**:

1. **Given** ba mặt hàng vật tư bếp, **When** mở tab Vật tư bếp, **Then** thấy nước rửa chén theo thùng, bao bóng loại 1 lít theo kg và bao tay gỏi theo kg.
2. **Given** báo cáo đồ khô và gia vị, **When** xem tổng nhóm, **Then** ba mặt hàng vật tư bếp không được cộng vào tổng nguyên liệu.
3. **Given** có lịch sử nhiều lần nhập một vật tư, **When** xem gợi ý nhập, **Then** thấy mức dùng/ngày và gợi ý kỳ tới cùng nhãn ước tính; không khẳng định đó là tồn hoặc tiêu hao thực tế.
4. **Given** có số kiểm tồn ban đầu và số kiểm tháng sau, **When** cập nhật báo cáo, **Then** dự báo dùng mốc tồn mới nhất để hiệu chỉnh lượng còn ước tính.
5. **Given** vật tư được mua theo hai quy cách khác nhau, **When** xem biến động giá, **Then** so giá đã quy về cùng đơn vị chuẩn và giữ thông tin mua gốc.

## Requirements

- **FR-001**: Tạo tab Vật tư bếp riêng cho nước rửa chén, bao bóng loại 1 lít và bao tay gỏi.
- **FR-002**: Không gộp vật tư bếp vào báo cáo nguyên liệu chế biến hoặc hàng bán kèm bàn.
- **FR-003**: Lưu ngày và lượng nhập của từng vật tư; dùng khoảng cách giữa các lần nhập để ước tính mức dùng bình quân/ngày.
- **FR-004**: Gợi ý thời điểm và lượng nhập kỳ tiếp theo từ mức dùng ước tính; hiển thị dữ liệu đầu vào và dấu hiệu “ước tính”. Khi chưa đủ lịch sử nhập thì không đưa ra con số có vẻ chính xác.
- **FR-005**: Cho nhập tồn ban đầu và kiểm lại hằng tháng hoặc đột xuất; dùng số kiểm mới nhất để hiệu chỉnh tồn ước tính và gợi ý nhập.
- **FR-006**: Lưu giá và quy cách mua thực tế từng lần nhập; quy đổi về cùng đơn vị chuẩn để so với lần mua trước của cùng mặt hàng.
- **FR-007**: Chỉ quản lý hoặc chủ quán được nhập và sửa dữ liệu vật tư; lưu lịch sử sửa với người thực hiện và thời điểm.
- **FR-008**: Gắn lịch sử nhập và kiểm vào ca thu ngân hiện có để đối chiếu theo ngày kinh doanh.

## Open Questions

- Cách ghi nhận vật tư hỏng hoặc bỏ đi.
- Quy cách thực tế của nước rửa chén theo thùng và cách quy đổi giá khi thay đổi đóng gói.


## Cập nhật quy tắc ngày 2026-11-05

Ngày kho do quản lý chọn khi nhập; không phụ thuộc giờ mở hoặc khóa ca thu ngân trong ứng dụng. Ô chưa nhập khác số 0. Quy tắc này thay thế mọi câu gắn ngày kho với ca thu ngân ở trên.

