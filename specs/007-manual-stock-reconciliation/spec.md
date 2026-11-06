# Feature Specification: Đối chiếu kho nhập tay theo ngày

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nhập từng mặt hàng (Priority: P1)

Quản lý chọn ngày và mốc đầu hoặc cuối ngày, rồi nhập những mặt hàng đã kiểm. Không cần mở hoặc đóng ca trên ứng dụng. Ô trống nghĩa là chưa kiểm; số 0 nghĩa là đã kiểm và không có hàng.

**Independent Test**: Lưu một mặt hàng, mở lại trang và xác nhận những mặt hàng khác vẫn trống.

**Acceptance Scenarios**:

1. **Given** A chưa nhập, **when** quản lý chỉ lưu B, **then** A vẫn trống và B giữ số đã nhập.
2. **Given** đã kiểm A và không có hàng, **when** nhập 0, **then** A được ghi là 0, khác trạng thái chưa nhập.
3. **Given** A đã lưu, **when** quản lý sửa A, **then** số mới được dùng ở lần tính tiếp và lịch sử ghi người, thời điểm sửa.

### User Story 2 - Bấm tính kết quả (Priority: P1)

Sau khi nhập, quản lý chủ động bấm “Tính kết quả”. Từng mặt hàng đủ số có tồn dự kiến và chênh lệch. Mặt hàng thiếu số hiện “Chưa có dữ liệu”.

**Independent Test**: Cùng ngày có một mặt hàng đủ số và một mặt hàng thiếu số; chỉ mặt hàng đủ số có chênh lệch.

**Acceptance Scenarios**:

1. **Given** A đủ tồn đầu, số nhập, số bán đã đồng bộ và tồn cuối, **when** bấm tính, **then** A có tồn dự kiến và chênh lệch.
2. **Given** B thiếu một đầu vào, **when** bấm tính, **then** B hiện số đã biết và phần chưa tính hiện “Chưa có dữ liệu”.
3. **Given** số đã lưu được sửa, **when** bấm tính lại, **then** kết quả dùng số mới.
4. **Given** hóa đơn chưa đồng bộ đủ, **when** bấm tính, **then** không kết luận thất thoát từ lượng bán chưa chắc chắn.

### User Story 3 - Kiểm thùng và lon/chai lẻ (Priority: P2)

Quản lý nhập tồn cuối bằng số thùng nguyên và số lon/chai lẻ; ứng dụng đổi sang tổng đơn vị.

**Independent Test**: 2 thùng 24 lon và 3 lon lẻ cho kết quả 51 lon.

**Acceptance Scenarios**:

1. **Given** quy cách 24, **when** nhập 2 thùng và 3 lon lẻ, **then** tồn thực tế là 51 lon.
2. **Given** quy cách 24, **when** nhập 24 lon lẻ, **then** ứng dụng yêu cầu đổi thành một thùng.

### Edge Cases

- Không có tồn cuối hôm trước: tồn đầu của mặt hàng mặc định là 0; quản lý vẫn có thể sửa số này nếu đang có hàng thực tế.
- Không có hàng nhập: quản lý nhập 0 cho mặt hàng muốn tính; để trống nghĩa là chưa khai báo.
- Chỉ nhập thùng hoặc chỉ nhập đơn vị lẻ ở cuối ngày: ô còn lại được hiểu là 0 cho mặt hàng đó.
- Sửa số sau lần tính: kết quả cũ phải được ẩn cho đến khi tính lại.
- Bàn còn mở hoặc đồng bộ CUKCUK lỗi: chênh lệch cuối cùng ở trạng thái chờ xác minh.
- Ngày qua 0 giờ: dùng ngày quản lý chọn; không suy ngày từ ca thu ngân.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Chủ quán hoặc quản lý MUST được nhập từng mặt hàng ở mốc đầu và cuối ngày, không bắt buộc nhập đủ danh mục.
- **FR-002**: Ứng dụng MUST phân biệt chưa nhập với số 0 đã xác nhận trong lưu trữ, giao diện và kết quả.
- **FR-003**: Nhập kho và tính kết quả MUST không phụ thuộc giờ mở hoặc khóa ca thu ngân.
- **FR-004**: Ứng dụng MUST có nút “Tính kết quả” riêng và tính lại từ số liệu mới nhất của ngày đã chọn.
- **FR-005**: Tồn dự kiến của hàng bán trực tiếp MUST bằng tồn đầu cộng nhập và điều chỉnh hợp lệ, trừ số bán đã đồng bộ.
- **FR-006**: Chênh lệch MUST bằng tồn thực tế trừ tồn dự kiến và chỉ hiện khi số nhập, số bán và tồn cuối của mặt hàng đó xác định. Nếu chưa có tồn hôm trước, tồn đầu mặc định là 0.
- **FR-007**: Mặt hàng thiếu đầu vào MUST hiện “Chưa có dữ liệu”; mặt hàng đủ dữ liệu vẫn được tính.
- **FR-008**: Hàng nhập đầu ngày MUST nhập theo thùng; tồn cuối MUST cho nhập thùng nguyên và đơn vị lẻ nhỏ hơn một thùng.
- **FR-009**: Số kiểm lịch sử MUST giữ nguyên tổng đơn vị khi nâng cấp.
- **FR-010**: Chỉ chủ quán hoặc quản lý MUST được nhập, sửa số kiểm; lịch sử sửa MUST có người và thời điểm.
- **FR-011**: Khi còn bàn mở hoặc hóa đơn chưa đồng bộ đủ, ứng dụng MUST không hiển thị kết luận thất thoát cuối cùng.
- **FR-012**: Ngày trên biểu mẫu MUST do quản lý chọn, không tự đổi theo ca thu ngân. Theo quy tắc hiện tại, chỉ ngày hiện tại được nhập hoặc sửa.
- **FR-013**: Màn nhập hàng MUST có ô tìm nhanh theo tên hoặc mã mặt hàng; lọc danh sách không được làm mất số đã gõ ở dòng khác.
- **FR-014**: Bảng nhập MUST ưu tiên tên mặt hàng và giấu mã khỏi cột hiển thị, nhưng vẫn dùng mã để nhận diện và tìm kiếm.
- **FR-015**: Danh sách nhập MUST nằm trong vùng cuộn gọn với tiêu đề cột luôn nhìn thấy khi cuộn.

### Key Entities *(include if feature involves data)*

- **Mặt hàng**: mã, tên, đơn vị và số đơn vị mỗi thùng.
- **Hàng nhập đầu ngày**: ngày, mặt hàng, số thùng, tổng đơn vị, người và thời điểm lưu.
- **Số kiểm cuối ngày**: ngày, mặt hàng, thùng nguyên, đơn vị lẻ, tổng đơn vị, người và thời điểm lưu.
- **Tồn đầu ngày**: số cuối ngày trước hoặc số quản lý khai báo khi thiếu lịch sử.
- **Kết quả đối chiếu**: các đầu vào, trạng thái dữ liệu, tồn dự kiến, tồn thực tế và chênh lệch nếu đủ dữ liệu.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Quản lý lưu được một mặt hàng mà không nhập các mặt hàng khác.
- **SC-002**: Trong các kịch bản kiểm thử, ô trống không bao giờ hiển thị như số 0 đã xác nhận.
- **SC-003**: Hai thùng 24 lon và 3 lon lẻ luôn cho tồn 51 lon.
- **SC-004**: Thiếu số nhập, tồn cuối hoặc dữ liệu bán của một mặt hàng thì chênh lệch của mặt hàng đó luôn là “Chưa có dữ liệu”; thiếu tồn hôm trước được tính là 0 theo yêu cầu.
- **SC-005**: Người đã biết số kiểm có thể lưu một mặt hàng và xem kết quả trong dưới 2 phút.
- **SC-006**: Người quản lý tìm được một mặt hàng theo tên hoặc mã trong dưới 10 giây mà không phải cuộn qua toàn bộ danh sách.

## Assumptions

- Dùng ngày do quản lý chọn trên biểu mẫu, không dùng mốc mở/đóng ca trong ứng dụng.
- Ngày đầu dùng mặc định tồn đầu 0; quản lý có thể sửa khi có tồn thực tế từ trước.
- Đặc tả này thay thế quy tắc gắn kho vào ca thu ngân và bắt nhập đủ danh mục của đặc tả 002. Các quy tắc danh mục, cảnh báo bàn và quy cách không xung đột vẫn giữ nguyên.
