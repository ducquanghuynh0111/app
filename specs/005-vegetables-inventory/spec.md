# Feature Specification: Kiểm kê rau và hàng tươi

**Status**: Đang làm rõ yêu cầu
**Input**: Chủ quán muốn tab Rau riêng trong phần Kho; quy trình kiểm, danh mục và cách tính cần xác nhận.

## Clarifications

### Session 2026-11-05

- Q: Kiểm số rau còn thực tế vào thời điểm nào? → A: Cuối mỗi ca kinh doanh sau khi đóng hết bàn; ghi rau nhập và rau hỏng trong ca.
- Q: Rau dùng trong ca chỉ tính từ số kiểm hay so thêm định mức theo món CUKCUK? → A: Tính lượng dùng thực tế và so thêm định mức theo món.
- Q: Có nhập rau và giá mỗi ngày, cảnh báo biến động không? → A: Chủ quán sẽ cung cấp danh sách rau nhập hằng ngày cùng giá; cảnh báo khi giá thay đổi và lượng dùng tăng giữa các tuần.
- Q: Cảnh báo tăng lượng rau giữa các tuần dựa trên chỉ số nào? → A: Cảnh báo riêng cả tổng lượng dùng thực tế và phần dùng vượt định mức theo số món đã bán.
- Q: Ngưỡng tăng nào bật cảnh báo lượng rau theo tuần? → A: Mặc định tăng trên 10%, quản lý chỉnh được theo từng loại rau; mức tăng nhỏ hơn vẫn hiển thị trong báo cáo.
- Q: Mẫu danh sách rau nhập hằng ngày có cấu trúc gì? → A: Chủ quán cung cấp ảnh phiếu nhà cung cấp với tên hàng, số lượng, đơn giá và thành tiền; nhiều dòng mẫu để trống và đơn vị không in trên mọi dòng.
- Q: Dòng mẫu “Sả 3, đơn giá 13, thành tiền 39” tính như thế nào? → A: 3 kg nhân 13.000 đồng/kg bằng 39.000 đồng; số tiền trên phiếu viết theo nghìn đồng.
- Q: Mỗi ngày nhập phiếu rau bằng ảnh hay nhập tay? → A: Chỉ nhập tay từ phiếu; ảnh dùng làm mẫu tham khảo, không cần tự nhận chữ viết tay.
- Q: Tab Rau chỉ theo dõi rau hay mọi thực phẩm tươi trên phiếu? → A: Theo dõi tất cả thực phẩm tươi trên phiếu, chia nhóm rau, trái cây, nấm/đậu hũ và nhóm phù hợp khác khi có mặt hàng thực tế.
- Q: Màn nhập tay lấy đơn vị số lượng và đơn giá từ đâu? → A: Tự điền đơn vị chuẩn từ danh mục mặt hàng, cho sửa theo quy cách mua thực tế ở từng lần nhập.
- Q: Đã có bảng định mức hàng tươi theo món CUKCUK chưa? → A: Chưa có; cần cho tạo và cập nhật định mức dần trong phần mềm.
- Q: Ai nhập và sửa số liệu kho? → A: Chỉ quản lý hoặc chủ quán.
- Q: Ca kinh doanh của Kho theo mốc nào? → A: Dùng ca thu ngân hiện có; ca qua 0 giờ vẫn thuộc ngày bắt đầu ca.

## User Scenarios & Testing

### User Story 1 — Theo dõi rau theo ngày (P1)

Quản lý hoặc chủ quán ghi lượng hàng tươi nhập và hỏng trong ca, rồi kiểm số còn thực tế cuối ca sau khi đóng hết bàn.

Mỗi ngày ghi từng mặt hàng tươi đã nhập, số lượng và giá mua. Cuối ca, lượng dùng thực tế được tính từ số kiểm; lượng dùng theo định mức được tính từ số món bán trên CUKCUK và công thức của từng món. Quản lý xem hai con số cùng biến động giá và lượng dùng theo tuần.

**Acceptance Scenarios**:

1. **Given** ca còn bàn đang mở, **When** nhân viên muốn chốt kiểm rau cuối ca, **Then** chưa cho chốt và nêu rõ bàn còn mở.
2. **Given** đã đóng hết bàn, **When** kiểm rau cuối ca, **Then** lưu số rau còn thực tế theo ca kinh doanh, kể cả ca qua 0 giờ.
3. **Given** có số món CUKCUK và định mức rau theo món, **When** đồng bộ đủ hóa đơn của ca, **Then** hiển thị lượng rau dùng theo định mức bên cạnh lượng dùng thực tế, không trộn hai số.
4. **Given** rau đã có giá mua lần trước, **When** nhập giá mới khác giá cũ, **Then** hiển thị cảnh báo giá tăng hoặc giảm và mức chênh lệch.
5. **Given** có hai kỳ tuần đủ dữ liệu kiểm và hóa đơn/định mức đầy đủ, **When** lượng rau dùng thực tế hoặc phần vượt định mức kỳ sau tăng theo ngưỡng đã chốt, **Then** hiển thị hai cảnh báo riêng với tên mặt hàng và số tăng.
6. **Given** món chưa khai định mức hàng tươi, **When** xem đối chiếu món hoặc cảnh báo vượt định mức, **Then** hiển thị “Chưa đủ dữ liệu định mức” và không tính phần vượt cho món đó.

## Requirements

- **FR-001**: Ghi rau nhập, rau hỏng và tồn rau thực tế theo ca kinh doanh.
- **FR-002**: Chỉ chốt số kiểm rau cuối ca sau khi mọi bàn đã đóng; ca qua 0 giờ vẫn thuộc ngày bắt đầu ca.
- **FR-003**: Ghi lượng và giá mua rau theo từng mặt hàng, từng ngày; lưu lịch sử giá để so với lần mua trước của cùng mặt hàng.
- **FR-004**: Tính lượng rau dùng thực tế từ tồn đầu, rau nhập, rau hỏng và tồn cuối; tính riêng lượng rau theo định mức món CUKCUK khi có đủ công thức và hóa đơn đồng bộ.
- **FR-005**: Cảnh báo khi giá mua thay đổi so với lần mua trước; báo tăng/giảm và số tiền chênh lệch theo cùng đơn vị.
- **FR-006**: Tổng hợp lượng rau dùng theo tuần; cảnh báo riêng khi tổng lượng dùng thực tế tăng và khi phần dùng vượt định mức tăng trên 10% mặc định so với tuần trước. Quản lý chỉnh ngưỡng riêng từng loại rau; mức tăng thấp hơn vẫn hiển thị trong báo cáo. Không so tuần thiếu dữ liệu như tuần đầy đủ.
- **FR-007**: Có màn hình nhập tay ngày phiếu, tên hàng, nhóm hàng tươi, số lượng, đơn vị, đơn giá và thành tiền; chỉ lưu dòng người dùng đã nhập và xác nhận, không tạo giao dịch từ các dòng mẫu để trống trên phiếu giấy.
- **FR-008**: Với phiếu dùng đơn vị nghìn đồng, quy đổi đơn giá và thành tiền sang đồng khi lưu; đối chiếu số lượng nhân đơn giá với thành tiền, báo dòng không khớp để người dùng kiểm tra.
- **FR-009**: Theo dõi mọi thực phẩm tươi mua trên phiếu trong cùng tab, phân nhóm rau, trái cây, nấm/đậu hũ và nhóm phù hợp khác; không chỉ giới hạn các loại rau lá.
- **FR-010**: Mỗi mặt hàng tươi có đơn vị chuẩn; màn nhập tay tự điền và cho sửa đơn vị/quy cách của lần mua, giữ dữ liệu gốc và quy đổi về đơn vị chuẩn trước khi so giá hoặc lượng dùng.
- **FR-011**: Cho chủ quán/quản lý tạo và cập nhật định mức hàng tươi theo mã món CUKCUK dần. Chỉ tính lượng lý thuyết và cảnh báo vượt định mức cho phần doanh số có định mức đầy đủ; thiếu định mức phải hiển thị rõ và không xem như mức dùng bằng 0.
- **FR-012**: Chỉ quản lý hoặc chủ quán được nhập và sửa dữ liệu hàng tươi; lưu lịch sử sửa với người thực hiện và thời điểm.
- **FR-013**: Gắn hàng nhập, hóa đơn và số kiểm hàng tươi vào ca thu ngân hiện có; ca qua 0 giờ vẫn dùng ngày bắt đầu ca.

## Open Questions

- Đơn vị mua/kiểm cho từng mặt hàng ngoài ví dụ sả đã xác nhận theo kg.
- Ngày và giờ của các phiếu mẫu chưa xác định đủ để ghi thành giao dịch thật.
- Ngưỡng cảnh báo tăng cho hai chỉ số lượng rau theo tuần.
- Danh sách món CUKCUK và định mức hàng tươi sẽ được khai dần; cần chốt ai nhập và ai duyệt định mức.
- Có đề xuất lượng rau cần nhập ngày tới hay không.


## Cập nhật quy tắc ngày 2026-11-05

Ngày kho do quản lý chọn khi nhập; không phụ thuộc giờ mở hoặc khóa ca thu ngân trong ứng dụng. Ô chưa nhập khác số 0. Quy tắc này thay thế mọi câu gắn ngày kho với ca thu ngân ở trên.

