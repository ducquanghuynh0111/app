# Khu, bàn và rà soát sai lệch order

## Bổ sung: xem bàn đã đóng trong Thống kê

- Mục Thống kê cho chọn bàn đang mở hoặc hóa đơn đã đóng theo ngày kinh doanh và khu. Với bàn đã đóng, chỉ lấy hóa đơn đã thanh toán trong báo cáo sau ca; nếu ngày chưa có báo cáo, tính báo cáo sau khi bàn CUKCUK đã đóng hết.
- Mỗi lượt hóa đơn hiện riêng dưới số bàn, gồm mã hóa đơn, toàn bộ dòng món cuối cùng CUKCUK trả về, số lượng và đơn vị. Một bàn dùng nhiều lần trong ngày có nhiều lượt riêng; không hiện khách hàng hoặc thông tin thanh toán.
- Quản lý ghi chú riêng từng hóa đơn dưới số bàn, kèm giờ hóa đơn CUKCUK để phân biệt các lượt dùng cùng bàn; ghi chú không gộp theo bàn và được giữ khi tính lại báo cáo cùng ngày. `RefDate` là giờ phát sinh hóa đơn, không được gọi là giờ đóng bàn chính xác khi API không trả trường đó. Báo cáo cũ thiếu chi tiết cần tính lại.
- Danh sách món là trạng thái cuối cùng trên hóa đơn đã thanh toán; không suy đoán lịch sử món đã hủy khi CUKCUK không trả dữ liệu đó.

## Bổ sung: thống kê theo khu

- Thống kê order bàn đang mở nằm trong mục riêng trên thanh điều hướng. Quản lý chọn một khu rồi bấm xem; chỉ lúc đó mới tải lại order từ CUKCUK.
- Thẻ khu không có nút Thống kê. Kết quả của khu đã chọn trình bày thành danh sách nhóm Bia, Nước, Đồ ăn kèm và Thuốc; tên mặt hàng và số lượng giữ đúng quy cách đang dùng.

## Bổ sung: bố cục và sửa cấp thuốc

- Trên màn hình rộng, mỗi hàng có tối đa ba thẻ khu; khu thứ tư xuống hàng mới. Trên màn hình hẹp, thẻ khu giảm còn hai hoặc một cột để không phải cuộn ngang.
- Các bàn trong mỗi khu hiển thị thành các ô phân bố đều theo chiều ngang. Bấm ô bàn mở hộp thoại riêng có tên mặt hàng, số lượng đã order theo Bia, Nước, Bánh tráng, Đậu phộng và Thuốc; nhóm chưa gọi hiện 0. Đóng hộp thoại quay về danh sách khu.
- Trong phần thuốc cấp và đối chiếu sau ca, mỗi loại thuốc nằm ở một khối riêng; Đã lấy, Đã order, Đã trả kho và Chênh lệch nằm trên từng dòng.
- Mỗi loại thuốc trong thẻ khu có nút + tăng một gói và nút − giảm một gói khi nhập nhầm; không cho âm, mỗi lần sửa có nhật ký.
- Ba thẻ khu cùng một hàng trên màn hình rộng; khu tiếp theo xuống hàng mới, chữ và nút không bị đè hoặc cắt.
- Dòng thuốc dùng nhãn ngắn, số đã lấy và hai nút trên cùng một hàng; tên nhân viên vẫn thấy trên thẻ.

## Bổ sung: đối chiếu sau ca

- Quản lý chọn ngày kinh doanh và bấm tính sau khi mọi bàn CUKCUK đã đóng. Không yêu cầu mở hoặc đóng ca trên ứng dụng này. Hóa đơn sau nửa đêm trước giờ cắt ngày thuộc ngày kinh doanh trước.
- Tồn dự kiến từng mặt hàng = tồn cuối lần kiểm trước + nhập hôm nay + hàng trả về kho − hỏng/tặng − số đã bán theo hóa đơn đã thanh toán. Nếu thiếu tồn trước, nhập, tồn cuối hoặc không xác định được đơn vị CUKCUK, hiển thị chưa đủ dữ liệu; không mặc định tồn trước bằng 0.
- Báo cáo từng khu cộng số bia, nước, bánh tráng, đậu phộng, thuốc theo các hóa đơn của bàn được gán khu; bia có tên loại và số thùng + lon/chai lẻ; thuốc có số cây + gói lẻ, mỗi cây 10 gói. Quy cách bia lấy từ danh mục.
- Mỗi hóa đơn của bàn được xét độc lập. Thiếu order bia, bánh tráng hoặc đậu phộng được ghi thành dấu hiệu để quản lý xác minh, kể cả khi bàn đó có hóa đơn khác đã order đủ. Hóa đơn không rõ bàn, chưa gán khu, mã hàng chưa ghép hoặc đơn vị chưa rõ không được dùng để kết luận nhân viên vi phạm.
- Quản lý nhập thuốc đã cấp, trả lại và còn tại khu theo cây và gói lẻ. Chênh lệch = đã cấp − trả lại − còn tại khu − số gói đã order trên hóa đơn; thiếu bất kỳ số nhập nào thì chưa đủ dữ liệu.
- Báo cáo lưu ảnh chụp kết quả và tên khu tại thời điểm tính; quản lý ghi chú xác minh cho từng hóa đơn cần xem. Thay đổi cấu hình khu về sau không sửa báo cáo đã lưu.
- Chỉ chủ/quản lý được tính báo cáo, nhập thuốc cấp khu và ghi chú. Nút tính chỉ gọi CUKCUK khi người dùng bấm.
- Không có khối “Đối chiếu sau ca” riêng trên màn Khu & rà soát. Nút tính đặt ở đầu màn; kết quả order, bàn cần xác minh và form thuốc cấp/trả/còn nằm trong từng thẻ khu. Không lặp lại bảng tồn kho toàn quán ở màn này.
- Các mặt hàng sau ca trong thẻ khu chia thành Bia, Rượu, Nước, Đồ ăn kèm và Thuốc, mỗi nhóm có tiêu đề riêng; nhóm không có hàng không cần hiện.
- Mỗi thẻ khu mang tên nhân viên có đúng hai dòng cấp thuốc con ngựa (TNN) và con mèo (TM). Bấm dấu + ghi thêm đúng 1 gói vào số đã lấy của ngày kinh doanh hiện tại và có dấu vết người/thời gian; không cần nhập cây để ghi cấp thuốc.
- Trong ca, nếu số gói đã lấy lớn hơn số gói thuốc tương ứng đã order ở các bàn đang mở của khu tại lần tải CUKCUK gần nhất, tô đỏ để nhắc kiểm tra. Đây là cảnh báo tạm thời vì bàn đóng không nằm trong danh sách đang mở; chỉ tải lại order khi mở màn hoặc bấm cập nhật, không quét nền.
- Cuối ca, quản lý ghi số gói thuốc trả về kho theo từng khu. Báo cáo khu hiển thị chênh lệch = đã lấy − đã trả kho − số đã bán theo hóa đơn thanh toán của khu; chênh lệch khác 0 tô đỏ và cần xác minh. Tồn thực tế cuối ca được đếm tại kho trong tab Kho, không yêu cầu đếm thuốc còn ở khu.

## User Scenarios

1. Chủ quán tạo khu và gán từng bàn vào đúng một khu; có thể chuyển bàn sang khu khác mà không mất lịch sử kiểm tra.
2. Chủ quán phân công nhân viên phụ trách khu trong một khoảng thời gian. Nhiều nhân viên có thể cùng phụ trách; thiếu phân công phải được hiển thị rõ.
3. Quản lý mở màn rà soát để thấy bàn đang mở thiếu bia hoặc thiếu bánh tráng/đậu phộng, được xếp theo khu và người phụ trách.
4. Quản lý kiểm thực tế một bàn, nhập số bia, rượu, nước, bánh tráng, đậu phộng và thuốc đang thấy; phần mềm so với order đang mở từ CUKCUK và lưu bằng chứng tại thời điểm kiểm.
5. Chủ quán xem các trường hợp nghi vấn theo khu, bàn, nhân viên và thời gian; có thể ghi nhận kết quả xác minh mà không tự động kết luận hoặc trừ lương.

## Functional Requirements

- **FR-001**: Chỉ chủ quán/quản lý được tạo và sửa khu; tên khu trên màn hình là tên nhân viên phụ trách, không trùng trong cùng chi nhánh.
- **FR-002**: Mỗi nhãn bàn thuộc tối đa một khu tại một thời điểm; chuyển khu có nhật ký người và thời gian.
- **FR-003**: Màn hình chỉ có các thẻ khu. Bấm Thêm khu mở thẻ nhập tên nhân viên và các số bàn; bấm thẻ đã lưu mở phần sửa tên, thêm, sửa hoặc bỏ số bàn.
- **FR-004**: Ô bàn chỉ nhận số dương; màn hình hiển thị "Bàn" và số. Ghép bàn đang mở từ CUKCUK theo số dù nhãn API có hoặc không có tiền tố "Bàn". Bàn chưa ghép và bàn thiếu mã món phải hiển thị là chưa xác định.
- **FR-005**: Bàn đang mở thiếu bia hoặc thiếu bánh tráng/đậu phộng được tô đỏ ngay trên thẻ khu. Đây là cảnh báo thiếu order, chưa phải kết luận nhân viên mang hàng sai.
- **FR-006**: Lần kiểm thực tế chỉ do chủ quán/quản lý ghi cho bàn đang mở. Mỗi nhóm số lượng là số nguyên không âm; ô trống nghĩa là chưa kiểm và không được coi là 0.
- **FR-007**: Tại thời điểm kiểm, phần mềm lấy lại order CUKCUK, lưu số kiểm thực tế và số order theo từng nhóm. Chỉ báo nghi vấn khi số thực tế lớn hơn số đã order, dữ liệu món đã ghép đầy đủ và bàn không ghép nhiều bàn.
- **FR-008**: Một nghi vấn gắn với tất cả nhân viên đang được phân công khu lúc kiểm, dưới nhãn "cần xác minh"; không gắn nhân viên nếu không có phân công hoặc chưa xác định khu.
- **FR-009**: Chủ quán/quản lý có thể xác nhận "đã giải thích" hoặc "cần xử lý" kèm ghi chú; không tự động phạt/trừ lương.
- **FR-010**: Chỉ gọi CUKCUK khi mở màn hình, sau thao tác sửa cấu hình hoặc khi cần dữ liệu mới; không có polling nền mới.
- **FR-011**: Lưu lịch sử kiểm và kết quả xác minh; khi đổi khu/phân công về sau, bằng chứng và người được gắn tại thời điểm kiểm không bị viết lại.
- **FR-012**: Mỗi khu có nút Thống kê, cộng số bia, nước (gồm nước ngọt), bánh tráng, đậu phộng và thuốc theo order của các bàn thuộc khu; ghi rõ phạm vi bàn đang mở và thời điểm dữ liệu.
- **FR-013**: Trong mỗi khu, mỗi bàn chiếm một hàng. Bấm hàng bàn mở đúng năm dòng bia, nước, bánh tráng, đậu phộng, thuốc và số lượng đã order trên CUKCUK; bàn chưa mở hiện dấu gạch thay số 0.
- **FR-014**: Chỉ bấm tên nhân viên mới mở phần sửa tên và số bàn; bấm bàn hoặc nút Thống kê không mở phần sửa.
- **FR-015**: Các bàn trong từng khu và danh sách bàn chưa gán được sắp theo giá trị số của bàn tăng dần (1, 2, 16), không theo thứ tự chữ cái.
- **FR-016**: Số lượng mở trong hàng bàn là Quantity theo order CUKCUK của nhóm hàng. Không tự đổi thùng thành lon/chai khi dữ liệu order chưa xác định được đơn vị của dòng món.
- **FR-017**: Hàng bàn liệt kê tên từng loại bia đã order. Nếu đơn vị order là thùng/két và mặt hàng có quy cách lon/chai mỗi thùng, quy đổi trước khi cộng; nếu order đã theo lon/chai, giữ nguyên. Thiếu quy cách thì hiện "Chưa rõ quy cách" và không công bố tổng lon/chai suy đoán.
- **FR-018**: Có chế độ dữ liệu mẫu chỉ hiển thị ở trình duyệt, không ghi vào cơ sở dữ liệu hoặc gọi CUKCUK khi mở bàn/thống kê mẫu. Mẫu gồm bàn thiếu bia, thiếu món kèm, đủ order, bia thùng quy đổi sang lon/chai và nhiều loại bia. Có nút trở lại dữ liệu thật; mẫu được gắn nhãn rõ và không cho sửa.
- **FR-019**: Nút Thống kê của mỗi khu hiện số bia theo từng mã/tên loại và quy đổi riêng bằng quy cách của loại đó: số thùng nguyên cộng lon/chai lẻ. Không gộp các loại bia thành một số lon tổng. Nếu chưa biết quy cách thì chỉ hiện số lon/chai và nhãn cần khai quy cách.
- **FR-020**: Trong Thống kê khu, Bia, Nước và Thuốc là ba mục có màu riêng, mặc định thu gọn. Bấm từng mục để xem từng mã/tên hàng và số lượng đã order. Bia và Nước dùng thùng cộng lon/chai lẻ theo quy cách từng hàng; Thuốc dùng cây cộng gói lẻ, 10 gói/cây nếu danh mục khai như vậy. Nước gồm cả nước uống và nước ngọt. Thiếu quy cách chỉ hiện đơn vị lẻ và yêu cầu khai quy cách, không tự suy đoán số thùng/cây.

## Success Criteria

- Quản lý có thể thêm và sửa tên nhân viên, các số bàn trực tiếp trong thẻ khu mà không cần sửa mã nguồn.
- Bàn chưa cấu hình vẫn xuất hiện với trạng thái "Chưa gán khu"; không có kết luận sai phạm.
- Với số kiểm thực tế lớn hơn số order, màn hình hiện đúng phần chênh lệch và danh sách người phụ trách tại thời điểm kiểm.
- Không có số kiểm thực tế thì không có cảnh báo "mang hàng chưa order".

## Assumptions

- Quy tắc thiếu bia/bánh tráng/đậu phộng hiện có tiếp tục áp dụng cho bàn đang mở.
- Số bàn nhập trên màn hình được chuẩn hóa trước khi so với nhãn bàn CUKCUK. Bàn ghép nhiều bàn không được tự tách số lượng.
- Quản lý quan sát số hàng tại bàn; việc kiểm này chưa chứng minh ai mang hàng ra, nên kết quả chỉ là nghi vấn để xem xét.
- Các loại vi phạm khác sẽ được đặc tả thêm sau khi chủ quán nêu quy tắc và nguồn bằng chứng.
