# Quy trình vận hành đề xuất cho một chi nhánh

Áp dụng cho quán có tám nhân viên phục vụ, năm nhân viên bếp và người tiếp thực. CUKCUK vẫn là nơi tạo order, in bill bếp và thanh toán. Sổ kiểm soát quán chỉ ghi bằng chứng đối soát, kho, ca làm và ngoại lệ; không bắt nhân viên nhập lại mọi order.

## Trách nhiệm

| Vai trò | Việc bắt buộc | Bằng chứng |
| --- | --- | --- |
| Phục vụ | Xác nhận bàn, món, số lượng và ghi chú với khách trước khi gửi order; mọi thay đổi/hủy ghi trong CUKCUK | Order và lịch sử thay đổi trên CUKCUK |
| Bếp | Chế biến theo phiếu in; báo ngay món hết, món sai, món trả lại | Phiếu bếp và báo cáo chế biến/trả lại |
| Tiếp thực | Đối chiếu bàn, món, số lượng trên phiếu bếp với món hoàn tất trước khi bưng; báo sai/thiếu/chậm | Mã bill hoặc số order trong sổ sự cố |
| Thu ngân | Chốt bill trong CUKCUK, ghi thu chi ngoài bill, đếm tiền cuối ca | Bảng kê hóa đơn, phiếu thu chi, tiền đếm |
| Kho/bếp phụ trách kho | Nhận hàng theo chứng từ; kiểm kê bia, thuốc và vật tư trọng yếu | Phiếu nhập, phiếu kiểm kê |
| Quản lý/chủ quán | Duyệt chênh lệch, khóa ca, xem xu hướng và xử lý sự cố | Nhật ký thao tác, báo cáo ca/kho |

## Đầu ca

1. Quản lý phân ca; nhân viên tự chấm vào trên ứng dụng.
2. Thu ngân mở ca tiền, ghi tiền mặt đầu ca. Người giao và người nhận cùng đếm.
3. Kho/bếp kiểm nhanh bia, thuốc và hàng dễ thất thoát; ghi phiếu kiểm kê nếu lệch tồn sổ.
4. Bếp báo món hết hoặc thiếu nguyên liệu để phục vụ cập nhật khả năng bán trong CUKCUK.

## Trong ca

1. Phục vụ xác nhận order với khách rồi gửi trong CUKCUK. Không nhận thay đổi chỉ bằng lời nói; sửa trên CUKCUK để bếp nhận phiếu mới.
2. Bếp làm theo phiếu in. Khi món xong, tiếp thực kiểm đúng bàn, đúng tên món, đúng số lượng và ghi chú.
3. Sai/thiếu/chậm món: ghi sự cố trong ứng dụng với mã bill/order, loại lỗi, mô tả, giá trị ước tính nếu có. Quản lý xác minh trước khi quy trách nhiệm.
4. Mọi khoản tiền không nằm trên bill CUKCUK phải vào sổ thu chi với lý do và chứng từ. Không bù chênh lệch bằng cách sửa số đầu ca.
5. Mọi hàng nhập có số lượng, đơn vị và chứng từ. Bia/thuốc bán ngoài bill phải ghi rõ lý do hoặc sửa bill CUKCUK theo quy trình quán.

## Cuối ca

1. Thu ngân lấy báo cáo Bảng kê hóa đơn hoặc tổng kết CUKCUK, phân tiền mặt và chuyển khoản. Hóa đơn in riêng lẻ chỉ là bằng chứng bill, không chứng minh đã nhận tiền.
2. Đếm tiền mặt thực tế; đối chiếu chuyển khoản bằng giao dịch thực nhận trong kỳ ca, tránh cộng số dư ngân hàng từ trước.
3. Nhập số liệu vào ca tiền; ứng dụng tính tiền kỳ vọng và chênh lệch. Ghi giải trình, chứng từ cho mọi chênh lệch.
4. Kiểm bia, thuốc cuối ca; kiểm nguyên liệu, nước chấm, gia vị theo lịch phù hợp với mức dùng. Phiếu kiểm kê phải được quản lý duyệt trước khi đổi tồn sổ.
5. Quản lý xem sự cố món đã chế biến/trả lại trong CUKCUK, đối chiếu với sự cố đã ghi, duyệt kiểm kê và khóa ca tiền.

## Nhịp kiểm tra

- Mỗi ca: tiền mặt, chuyển khoản, bia, thuốc, các sự cố order.
- Mỗi ngày: món hủy/trả, hàng dưới tồn tối thiểu, ca đi muộn, phiếu kiểm kê chờ duyệt.
- Mỗi tuần: nước chấm/gia vị theo đơn vị chuẩn, định lượng món, xu hướng chênh lệch và nguyên nhân lặp lại.

Tần suất và mức dung sai cần chỉnh sau một đến hai tuần đo thực tế. Chênh lệch là tín hiệu cần xác minh, không tự động chứng minh thất thoát hoặc lỗi của một nhân viên.

## Báo cáo CUKCUK nên xin quyền xuất

- Bảng kê hóa đơn với chi tiết hình thức thanh toán.
- Chi tiết doanh thu theo hóa đơn và mặt hàng.
- Số món gửi bếp, chế biến, trả lại và tính tiền.
- Hủy order/hủy món.

Khi có file Excel/CSV mẫu đã ẩn dữ liệu nhạy cảm, xây ánh xạ cột và đối chiếu tự động theo số hóa đơn/order. Trước lúc đó, CSV trong ứng dụng là mẫu trung gian chuẩn hóa.
