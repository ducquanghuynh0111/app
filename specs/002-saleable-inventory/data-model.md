# Mô hình dữ liệu

## Mặt hàng kiểm kê

- `code` là mã duy nhất, viết hoa khi đối chiếu; `group` thuộc bia, rượu, nước, thuốc, bánh tráng, đậu phộng.
- `units_per_carton` là số đơn vị/thùng; mặc định 24 nếu chưa rõ, HUDA chai 20, Budweiser lon 28, rượu 12 chai/thùng.
- `active=false` loại khỏi màn hiện tại nhưng không xóa phát sinh cũ.
- BATR thuộc bánh tráng; DAUPHONG và DAPH là hai mặt hàng riêng cùng nhóm đậu phộng.

## Bàn và dòng món

- Order có mã, trạng thái, nhãn bàn và các dòng món. Chỉ order còn mở thuộc loại phục vụ tại bàn được đưa vào danh sách.
- Dòng món có mã nguồn, mã món đã tra, tên, số lượng; chỉ cộng dòng chính, tránh cộng sở thích phục vụ hoặc dòng con.
- Một nhãn bàn ghép được giữ nguyên; không chia số lượng sang từng bàn thành phần khi nguồn không chỉ rõ.
- Trạng thái nhóm: `present` khi tổng > 0, `missing` khi tổng = 0 và mã đã ánh xạ đầy đủ, `unknown` khi danh mục còn thiếu mã cần thiết. Cảnh báo đỏ chỉ dựa trên tổng bia bằng 0, kể cả khi có rượu/nước; cảnh báo cam khi đã có bia nhưng thiếu hàng kèm.

## Kiểm kê và số chuyển sang

- Lượt kiểm gắn ca thu ngân và ngày bắt đầu ca; mốc đầu ghi số thùng nhập, mốc cuối ghi số thùng nguyên và số chai/lon lẻ. Số đơn vị cuối ca = thùng × quy cách + số lẻ, với 0 ≤ số lẻ < quy cách.
- Chỉ lưu kiểm cuối ca sau khi tất cả bàn đã đóng; trước khi lưu phải kiểm lại trạng thái bàn mới nhất. Ca qua 0 giờ vẫn thuộc ngày bắt đầu ca.
- Số chuyển sang ca hiện tại là giá trị điều chỉnh cho ca đó; không thay phiếu cuối của ca trước. Sửa quy cách tính lại lượt kiểm của ca hiện tại và để lại nhật ký.
- Trạng thái đối chiếu là `waiting_sync` khi đã kiểm nhưng hóa đơn CUKCUK chưa đồng bộ đủ; chỉ khi dữ liệu đủ mới tính chênh lệch. Không biểu diễn thiếu dữ liệu bằng 0.
- Chỉ chủ quán/quản lý được nhập và sửa số liệu kho; ghi người và thời điểm cho mỗi thay đổi.

## Bán theo bàn và trả/hủy

- Bán theo bàn gắn ngày kinh doanh, hóa đơn/bàn, mã mặt hàng và số lượng cuối có căn cứ.
- `cancelled_quantity` chỉ có giá trị khi có lịch sử hủy đáng tin theo dòng; nếu không là `unknown`, trình bày “Chưa có dữ liệu”.
