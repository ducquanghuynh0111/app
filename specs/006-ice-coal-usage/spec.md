# Feature Specification: Theo dõi nhập đá và than

**Status**: Đã chốt quy tắc nghiệp vụ chính
**Input**: Chủ quán muốn tab Đá và than chỉ thống kê số lượng sử dụng từng ngày.

## Clarifications

### Session 2026-11-05

- Q: Lượng đá và than được ghi thế nào? → A: Ghi số lượng nhập và ngày nhập; không tính tồn. Than nhập khi hết, đá nhập mỗi ngày. Dùng khoảng cách giữa các lần nhập để ước tính nhịp dùng; không gọi số nhập là số dùng thực tế.
- Q: Đá và than được ghi theo đơn vị nào? → A: Đá theo bao, than theo kg.
- Q: Ca kết thúc sau 0 giờ thì lượng dùng thuộc ngày nào? → A: Ngày bắt đầu ca kinh doanh.
- Q: Đá mua mỗi ngày có còn dư qua ngày sau không? → A: Hầu như dùng hết trong ngày; lượng nhập có thể dùng làm gần đúng cho lượng dùng ngày đó, phải ghi nhãn ước tính.
- Q: Ai nhập và sửa số liệu kho? → A: Chỉ quản lý hoặc chủ quán.
- Q: Ca kinh doanh của Kho theo mốc nào? → A: Dùng ca thu ngân hiện có; không tạo ca kho riêng.

## User Scenarios & Testing

### User Story 1 — Xem lượng đá và than dùng theo ngày (P1)

Quản lý hoặc chủ quán ghi ngày và lượng đá/than nhập. Đá thường nhập mỗi ngày; than nhập khi hết. Người quản lý xem lượng nhập theo ngày và khoảng cách giữa các lần nhập để ước tính nhịp dùng; không cần kiểm tồn.

**Acceptance Scenarios**:

1. **Given** nhân viên nhập đá hoặc than, **When** quản lý xem báo cáo, **Then** thấy lượng nhập theo từng mặt hàng và ngày/ca, không gắn nhãn “đã dùng thực tế”.
2. **Given** có ít nhất hai lần nhập than, **When** xem nhịp dùng, **Then** thấy số ngày giữa hai lần nhập và mức dùng/ngày ước tính từ lượng nhập, kèm nhãn ước tính.
3. **Given** có lượng đá nhập trong một ngày, **When** xem báo cáo, **Then** lượng dùng ước tính gần bằng lượng nhập ngày đó và không hiển thị như số dùng đã đo trực tiếp.

## Requirements

- **FR-001**: Có tab riêng cho đá và than, hiển thị lượng nhập theo từng ngày/ca.
- **FR-002**: Không tự suy ra lượng dùng từ định mức món ăn.
- **FR-003**: Nhân viên nhập ngày và số đá/than mua; không yêu cầu ghi số đã dùng trực tiếp hoặc kiểm tồn.
- **FR-004**: Đá ghi theo bao, than ghi theo kg; không cộng hai đơn vị thành một tổng lượng.
- **FR-005**: Ca qua 0 giờ vẫn ghi lượng đá và than dùng vào ngày bắt đầu ca kinh doanh.
- **FR-006**: Thống kê lượng nhập theo ngày/ca; tính khoảng cách giữa hai lần nhập và mức dùng/ngày ước tính, hiển thị rõ đây là ước tính. Không tính tồn kho hoặc theo dõi giá trong tab này.
- **FR-007**: Với đá hầu như hết mỗi ngày, dùng lượng nhập của ngày làm lượng dùng ước tính. Với than chỉ nhập khi hết, chia lượng nhập lần trước cho số ngày đến lần nhập kế tiếp để ước tính mức dùng/ngày của khoảng đó; chưa có lần nhập kế tiếp thì chưa có mức dùng xác nhận cho khoảng hiện tại.
- **FR-008**: Chỉ quản lý hoặc chủ quán được nhập và sửa dữ liệu đá, than; lưu lịch sử sửa với người thực hiện và thời điểm.
- **FR-009**: Gắn số nhập đá, than vào ca thu ngân hiện có để thống kê theo ngày bắt đầu ca.

## Open Questions

Không còn câu hỏi nghiệp vụ trọng yếu cho phạm vi thống kê nhập và ước tính dùng đá, than.


## Cập nhật quy tắc ngày 2026-11-05

Ngày kho do quản lý chọn khi nhập; không phụ thuộc giờ mở hoặc khóa ca thu ngân trong ứng dụng. Ô chưa nhập khác số 0. Quy tắc này thay thế mọi câu gắn ngày kho với ca thu ngân ở trên.

