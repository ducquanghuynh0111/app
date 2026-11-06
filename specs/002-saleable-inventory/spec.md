# Đặc tả: Kiểm kê hàng bán trực tiếp và hàng kèm bàn

## Bổ sung: đơn vị bán trong kết quả tồn kho

- Số bán từ hóa đơn CUKCUK phải được đổi về đơn vị kho của từng mặt hàng trước khi tính tồn dự kiến và chênh lệch; ví dụ 1 thùng bia 24 lon là 24 lon bán ra.
- Nếu đơn vị trên dòng hóa đơn trống hoặc không quy đổi được, số bán và chênh lệch của mặt hàng đó hiển thị dấu `-`, không tạo kết luận thất thoát sai.
- Màu bảng đối chiếu giữ ngưỡng đã chốt: 0 xanh, chênh lệch từ 1 đến 24 đơn vị cam, trên 24 đơn vị đỏ; cả thiếu và dư đều là chênh lệch cần kiểm tra.

## Bổ sung: màu nhóm và bố cục

- Chỉ tab kiểm kê hàng bán trực tiếp đang sẵn sàng sử dụng. Ba tab Đồ khô, gia vị; Rau; Đá, than bị vô hiệu hóa bằng kiểu hiển thị mờ, giữ tên ngắn và không cho mở từ giao diện cho đến khi quy trình tương ứng hoàn tất.
- Bia, Rượu, Nước, Đồ ăn kèm và Thuốc trong “Kiểm tra hàng” dùng cùng màu và tên nhóm như “Thống kê theo ngày”.
- Ba mục Kiểm tra hàng, Tồn kho và thất thoát, Thống kê theo ngày có tiêu đề, khoảng cách và đường phân tách rõ; mục Thống kê theo ngày có thể đóng gọn toàn bộ.
- Rà soát tên trùng từ danh mục CUKCUK hiện tại bằng thao tác chỉ đọc; chuẩn hóa hoa/thường, dấu tiếng Việt, dấu câu và khoảng trắng. Chỉ báo cáo tên và mã trùng, không tự gộp thêm mặt hàng.

## Bổ sung: nhập lẻ và mã trùng đã xác nhận

- Mốc đầu ngày cho nhập cả số thùng/cây và số lon/chai/gói lẻ, giống mốc cuối ngày; số nhập quy đổi = số thùng/cây × quy cách + số lẻ.
- Danh mục kiểm kê chỉ hiển thị mã chính DG, DAUPHONG, COCA, HUCH và BH cho năm mặt hàng đã xác nhận trùng. Mã cũ DIGI, DAPH, CC, BIAHUDACHAI và HL được giữ làm bí danh để order và hóa đơn CUKCUK vẫn cộng vào đúng mặt hàng; bản ghi lịch sử không bị xóa.
- Chưa tự gộp các tên bia gần giống khác khi chủ quán chưa xác nhận là cùng một mặt hàng.

**Feature directory**: `specs/002-saleable-inventory`  
**Created**: 2026-11-05  
**Status**: Đã chốt yêu cầu bàn và trả/hủy; cần xác nhận đơn vị kiểm kho của ba mã mới  
**Input**: Yêu cầu của chủ quán về bia, nước, thuốc, bánh tráng, đậu phộng, rượu và đối chiếu theo bàn.

## Clarifications

### Session 2026-11-05

- Q: Bạn muốn Spec Kit chốt yêu cầu phần nào trước? → A: Kiểm kê bia, nước, thuốc và hàng kèm bàn.
- Q: Bánh tráng và đậu phộng có được gọi thành hai dòng món riêng trên CUKCUK cho từng bàn không? → A: Có, đó là hai món riêng.
- Q: Hai mã món CUKCUK của bánh tráng và đậu phộng là gì? → A: Bánh tráng là BATR; đậu phộng là DAUPHONG hoặc DAPH.
- Q: DAUPHONG và DAPH đều là mã đậu phộng đang dùng hay chỉ một mã đúng? → A: Cả hai mã đều đang dùng cho đậu phộng.
- Q: Khi CUKCUK không có lịch sử hủy từng món, cột Trả/hủy nên hiển thị thế nào? → A: Hiển thị “Chưa có dữ liệu”, không tự suy đoán.
- Q: Rượu nhập theo chai hay theo thùng? → A: Nhập theo thùng, mỗi thùng 12 chai.
- Q: Cuối ngày còn thùng lẻ thì nhập tồn thế nào? → A: Hai ô riêng: số thùng và số chai/lon lẻ.
- Q: Bàn gọi rượu hoặc nước ngọt nhưng không có bia có bị cảnh báo đỏ không? → A: Có; chỉ bia mới làm bàn hết cảnh báo đỏ.
- Q: Cuối ngày còn bàn mở hoặc hóa đơn chưa đồng bộ thì có kiểm kê và tính thất thoát không? → A: Chỉ kiểm kê và tính toán sau khi tất cả bàn đã đóng.
- Q: Quán phục vụ qua 0 giờ thì ngày kiểm kê tính theo ngày lịch hay ca kinh doanh? → A: Theo ca kinh doanh, kết thúc khi đóng bàn cuối.
- Q: Đã đóng hết bàn nhưng hóa đơn CUKCUK chưa đồng bộ đủ thì có kiểm hàng không? → A: Cho lưu số kiểm thực tế trước, chỉ tính chênh lệch sau khi dữ liệu hóa đơn của ca đồng bộ đủ.
- Q: Ai nhập và sửa số liệu kho? → A: Chỉ quản lý hoặc chủ quán.
- Q: Ca kinh doanh của Kho theo mốc nào? → A: Dùng ca thu ngân hiện có trong phần mềm, không tạo ca kho riêng.

## User Scenarios & Testing

### User Story 1 — Biết bàn đang thiếu hàng kèm (P1)

Quản lý xem các bàn đang mở cùng số bia, nước, bánh tráng, đậu phộng và thuốc đã gọi; bấm vào bàn để xem chi tiết. Bàn chưa có bia màu đỏ, kể cả khi đã gọi rượu hoặc nước. Bàn có bia nhưng thiếu bánh tráng hoặc đậu phộng màu cam. Nếu thiếu cả bia và hàng kèm, màu đỏ ưu tiên.

**Independent Test**: Tạo ba bàn với các tổ hợp hàng khác nhau; danh sách chỉ chứa bàn còn mở, hiển thị đúng màu và số 0 cho mặt hàng chưa có.

**Acceptance Scenarios**:

1. **Given** bàn mở chưa có bia, dù đã gọi rượu hoặc nước, **When** tải danh sách, **Then** bàn màu đỏ và số bia là 0.
2. **Given** bàn có bia nhưng thiếu bánh tráng hoặc đậu phộng, **When** tải danh sách, **Then** bàn màu cam và chỉ rõ loại còn thiếu.
3. **Given** bàn đã đóng, **When** tải danh sách bàn đang mở, **Then** bàn đó không xuất hiện.
4. **Given** bàn gọi cùng một mặt hàng nhiều lần, **When** mở chi tiết bàn, **Then** hiển thị tổng lượng còn hiệu lực.

### User Story 2 — Nhập và kiểm hàng theo ngày (P1)

Quản lý hoặc chủ quán nhập số thùng nhận đầu ngày. Chỉ sau khi tất cả bàn đã đóng mới được kiểm cuối ngày: nhập số thùng nguyên và số chai/lon lẻ còn thực tế, rồi tính đối chiếu. Rượu có quy cách 12 chai/thùng. Chủ quán hoặc quản lý có thể sửa quy cách, số chuyển sang hôm nay và số nhập hôm nay ngay trong bảng.

**Independent Test**: Nhập số thùng, kiểm tra số lon/chai quy đổi; nhấp một ô, sửa và rời ô để lưu; xác nhận không tạo phiếu cho ca cũ đã khóa. Ca qua 0 giờ vẫn giữ ngày bắt đầu ca.

**Acceptance Scenarios**:

1. **Given** mốc đầu ngày, **When** mở bảng, **Then** số chưa nhập là 0 và chỉ hiện nút “Nhập hàng”.
2. **Given** mốc cuối ngày, **When** đổi mốc, **Then** chỉ hiện nút “Kiểm hàng”.
3. **Given** HUDA chai, Budweiser lon và rượu, **When** nhập số thùng, **Then** lần lượt quy đổi 20 chai/thùng, 28 lon/thùng và 12 chai/thùng.
4. **Given** ô được phép sửa, **When** nhấp một lần, thay số rồi rời ô, **Then** lưu và tính lại; ô giữ nguyên kích thước và khác hình thức với ô chỉ đọc.
5. **Given** cuối ngày còn 1 thùng rượu và 3 chai lẻ, **When** lưu kiểm hàng, **Then** tồn thực tế là 15 chai theo quy cách 12 chai/thùng.
6. **Given** còn ít nhất một bàn đang mở, **When** chọn kiểm cuối ngày, **Then** không cho lưu số kiểm hoặc tính thất thoát và chỉ rõ bàn cần đóng.
7. **Given** mọi bàn đã đóng nhưng hóa đơn CUKCUK chưa đồng bộ đủ, **When** lưu số kiểm, **Then** giữ số đếm và hiển thị trạng thái chờ đồng bộ; chưa tính chênh lệch. Khi dữ liệu đủ, hệ thống tính chênh lệch từ số kiểm đã lưu.

### User Story 3 — Đối chiếu tồn và truy số bán theo bàn (P1)

Quản lý xem số tồn hôm trước, số nhập, số bán theo hóa đơn, tồn dự kiến và tồn thực tế. Từ mỗi mặt hàng có thể xem bàn nào gọi bao nhiêu và thông tin trả/hủy nếu nguồn cung cấp.

**Independent Test**: Với dữ liệu bán và hai mốc kiểm đã biết, chênh lệch và màu đúng ngưỡng; tổng chi tiết theo bàn khớp số bán mặt hàng.

**Acceptance Scenarios**:

1. **Given** số chuyển sang, nhập, bán và tồn thực tế, **When** đối chiếu, **Then** tồn dự kiến bằng chuyển sang cộng nhập trừ bán và cộng/trừ điều chỉnh đã ghi.
2. **Given** chênh lệch 0, từ 1 đến 24, hoặc trên 24 đơn vị, **When** xem bảng, **Then** lần lượt màu xanh, cam hoặc đỏ.
3. **Given** mặt hàng bán ở nhiều bàn, **When** mở chi tiết, **Then** có danh sách bàn và số lượng để đối chiếu với tổng.
4. **Given** nguồn không có lịch sử trả/hủy theo dòng món, **When** mở chi tiết, **Then** cột “Trả/hủy” hiển thị “Chưa có dữ liệu”, không hiển thị số 0 hoặc số ước tính.

### Edge Cases

- Ca đầu chưa có kiểm kê cuối ca trước: số chuyển sang là 0 cho đến khi chủ quán/quản lý sửa tại ca hiện tại.
- Đổi quy cách phải tính lại lượng quy đổi của các lượt kiểm trong ca hiện tại và ghi lịch sử.
- Hàng chưa rõ quy cách tạm đặt 24 lon/chai mỗi thùng; người có quyền sửa khi hàng thực tế khác.
- Cuối ngày, số chai/lon lẻ phải nhỏ hơn quy cách thùng của mặt hàng; số tồn thực tế bằng số thùng nguyên nhân quy cách cộng số lẻ.
- Bàn ghép hoặc hóa đơn tách chỉ hiển thị thông tin có nguồn, không tự gán món sang bàn khác.
- Bánh tráng và đậu phộng là hai món riêng trên CUKCUK; nếu chưa ánh xạ mã, phải báo chưa xác định thay vì kết luận bàn thiếu món.
- Một bàn có DAUPHONG, DAPH hoặc cả hai được tính là đã gọi đậu phộng; số lượng nhóm là tổng của hai mã, chi tiết vẫn giữ mã gốc.
- Thiếu dữ liệu bán hoặc đồng bộ chưa đủ phải báo rõ, chưa kết luận nguyên nhân thất thoát.
- Sau khi đóng hết bàn, thiếu dữ liệu đồng bộ không ngăn lưu số đếm thực tế; chỉ ngăn tính chênh lệch và kết luận thất thoát.
- Chỉ kiểm cuối ca sau khi mọi bàn đã đóng; trạng thái đóng bàn phải được kiểm tra lại trước lúc lưu. Chênh lệch còn chờ dữ liệu hóa đơn đầy đủ.
- Hóa đơn sau 0 giờ của ca chưa kết thúc thuộc ngày bắt đầu ca; không tự tách kiểm kê tại 0 giờ.
- Nếu nguồn chỉ có trạng thái hủy cả hóa đơn hoặc số lượng cuối của món, không suy ra lượng trả/hủy từng món; cột tương ứng hiển thị “Chưa có dữ liệu”.

## Requirements

### Functional Requirements

- **FR-001**: Hiển thị bàn đang mở và số lượng hiện tại của bia, nước, thuốc, bánh tráng, đậu phộng; bàn đóng không xuất hiện.
- **FR-002**: Bàn chưa có bia màu đỏ, dù có rượu hoặc nước; bàn có bia nhưng thiếu bánh tráng/đậu phộng màu cam; đỏ ưu tiên khi thiếu cả hai.
- **FR-003**: Có thể mở chi tiết bàn; mặt hàng chưa có hiển thị 0.
- **FR-004**: Tải bàn khi mở màn và khi yêu cầu tải lại; chỉ tự tải định kỳ nếu giới hạn nguồn dữ liệu đã xác nhận cho phép.
- **FR-005**: Đầu ngày ghi hàng nhập theo thùng, riêng thuốc được ghi theo cây và gói lẻ; cuối ngày ghi số thùng/cây nguyên và số đơn vị lẻ. Rượu quy đổi 12 chai/thùng; thuốc quy đổi 10 gói/cây.
- **FR-006**: Chỉ kiểm kê ca đang hoạt động hoặc vừa kết thúc, kể cả ca qua 0 giờ; không tạo hoặc sửa phiếu của ca cũ đã khóa.
- **FR-007**: Ô số chưa nhập hiển thị 0, nút tăng/giảm thay đổi 1, ô sửa có hình thức khác ô chỉ đọc và không làm xô bảng.
- **FR-008**: Chủ quán/quản lý nhấp một lần để sửa quy cách, số chuyển sang hoặc số nhập hôm nay; rời ô lưu giá trị hợp lệ và tính lại.
- **FR-009**: Quy cách mặc định 24 cho hàng chưa xác nhận; HUDA chai 20, Budweiser lon 28, rượu 12 chai/thùng và thuốc 10 gói/cây.
- **FR-010**: Chỉ chủ quán/quản lý được nhập hoặc sửa số liệu kho và quy cách; lưu lịch sử thay đổi, người thực hiện và thời điểm.
- **FR-011**: Tính tồn dự kiến và chênh lệch từng mặt hàng; màu theo ngưỡng 0/24/>24 đơn vị.
- **FR-012**: Cho xem số bán theo bàn từ từng mặt hàng và đối chiếu được tổng.
- **FR-013**: Hàng ngừng theo dõi không xuất hiện trong màn hiện tại nhưng giữ lịch sử.
- **FR-014**: Hiển thị trạng thái dữ liệu chưa đủ; không tự quy trách nhiệm thất thoát cho nhân viên.
- **FR-015**: Dựa trên BATR để xác định bánh tráng và cộng cả DAUPHONG lẫn DAPH để xác định số đậu phộng theo bàn; chi tiết vẫn cho biết mã gốc.
- **FR-016**: Cột trả/hủy theo món chỉ có số khi nguồn cung cấp được lịch sử đáng tin cậy theo dòng; nếu không, hiển thị dấu “-”.
- **FR-017**: Chặn lưu kiểm cuối ngày và chặn tính thất thoát khi còn bàn đang mở; kiểm tra trạng thái bàn mới nhất trước khi lưu và nêu rõ bàn cần đóng.
- **FR-018**: Gom giao dịch và số kiểm theo ca kinh doanh bắt đầu trước 0 giờ, kết thúc khi bàn cuối cùng của ca đóng.
- **FR-019**: Sau khi đóng hết bàn, cho lưu số kiểm dù hóa đơn chưa đồng bộ đủ; đánh dấu chờ đồng bộ và chỉ tính chênh lệch khi xác nhận đủ dữ liệu hóa đơn của ca.
- **FR-020**: Gắn số kiểm, hàng nhập và hóa đơn vào ca thu ngân hiện có; ca qua 0 giờ vẫn dùng ngày bắt đầu ca.
- **FR-021**: Danh mục kiểm hàng có TNn (Thuốc con ngựa) và TM (Thuốc con mèo); hai mặt hàng thuộc nhóm Thuốc, đơn vị Gói, mỗi cây quy đổi đúng 10 gói; mã CUKCUK được giữ nội bộ để đối chiếu hóa đơn.
- **FR-022**: Trong màn kiểm hàng và kết quả kho, ẩn cột mã; xếp mặt hàng theo Bia → Rượu → Nước (nước ngọt, nước uống) → Món phụ (bánh tráng, đậu phộng) → Thuốc, có nhãn nhóm rõ ràng.
- **FR-023**: Mỗi nhóm Bia, Rượu, Nước, Món phụ, Thuốc có nút Thêm mới; khi nhấp, form thêm hàng mở sẵn nhóm phù hợp và vẫn cho chọn phân nhóm trong Nước hoặc Món phụ.
- **FR-025**: Các nhóm mặt hàng trên màn kiểm hàng mặc định thu gọn; nhấp tiêu đề để mở/đóng mà không mất số đang nhập. Khi tìm mặt hàng, tự mở nhóm có kết quả và ẩn nhóm không khớp.
- **FR-024**: Các ô số liệu chỉ đọc chưa có nguồn hoặc chưa được ghi trong bảng tồn kho và chi tiết theo bàn hiển thị “-”, phân biệt với số 0 đã được kiểm/ghi; ô đang nhập giữ trạng thái trống cho đến khi người quản lý điền.

### Key Entities

- **Mặt hàng**: mã CUKCUK, tên, nhóm, đơn vị, quy cách, trạng thái theo dõi; BATR là bánh tráng, DAUPHONG và DAPH đều là đậu phộng.
- **Bàn đang mở**: nhãn bàn, trạng thái, thời điểm, các dòng hàng còn hiệu lực.
- **Lượt kiểm**: ngày, mốc đầu/cuối, mặt hàng, số thùng/chai, số quy đổi, người ghi.
- **Số chuyển sang hôm nay**: ngày, mặt hàng, số đơn vị, người sửa; không thay số kiểm ngày trước.
- **Phát sinh bán**: ngày kinh doanh, bàn/hóa đơn, mặt hàng, số lượng và thông tin trả/hủy nếu nguồn có.
- **Nhật ký sửa**: người thao tác, thời điểm, mục và loại thay đổi.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Với tối đa 100 bàn đang mở, quản lý xác định bàn thiếu hàng kèm từ một danh sách, không phải mở từng hóa đơn.
- **SC-002**: Mọi mặt hàng đang theo dõi có thể ghi số 0; lượng quy đổi đúng quy cách đã lưu.
- **SC-003**: 100% lần sửa quy cách, số chuyển sang và số nhập truy được người sửa và thời điểm.
- **SC-004**: Khi dữ liệu đầy đủ, mỗi mặt hàng có tồn dự kiến, tồn thực tế, chênh lệch; tổng theo bàn khớp tổng bán.
- **SC-005**: Sửa ô bằng một lần nhấp và độ rộng cột không đổi khi ô nhận focus.

## Assumptions

- Phần mềm bổ sung CUKCUK; CUKCUK vẫn là nguồn order và hóa đơn.
- Quán có một chi nhánh, tám nhân viên phục vụ, năm nhân viên bếp; máy quản lý bật trong giờ hoạt động.
- Chủ quán có tài khoản quản trị và quyền truy cập dữ liệu CUKCUK; tài liệu API công khai hiện mô tả trạng thái hủy hóa đơn và lượng cuối của món, chưa xác nhận lịch sử hủy từng dòng.
- TNn và TM là hai mã CUKCUK do chủ quán cung cấp. Chủ quán xác nhận cả hai loại thuốc đều có 10 gói trong mỗi cây.
- Phần đọc món trên máy tính bảng, thu chi và nhân sự thuộc các đặc tả khác.
