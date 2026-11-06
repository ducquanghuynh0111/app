# Hợp đồng hiển thị kiểm kê

## Danh sách bàn đang mở

Mỗi bàn có `table`, `quantities` theo nhóm, `missing_required`, `no_beer`, `combined_table`, và trạng thái dữ liệu `mapped` hoặc `unknown`. Mỗi dòng chi tiết giữ `code`, `name`, `quantity` và `group`.

- BATR được tính vào `rice_paper`.
- DAUPHONG và DAPH cùng tính vào `peanuts`; chi tiết không gộp mất mã.
- Nếu không nhận diện được một mã liên quan, trả `unknown` cùng số mã chưa ánh xạ; giao diện không khẳng định bàn thiếu.
- Bàn ghép giữ một nhãn bàn ghép như nguồn.
- `no_beer` là true khi tổng bia bằng 0; rượu, nước ngọt và nước uống không thay thế bia cho cảnh báo đỏ.

## Bảng kiểm theo ngày

Mỗi mặt hàng có mã, tên, nhóm, đơn vị, số chuyển sang, quy cách, số thùng đã nhập hoặc kiểm, số chai/lon lẻ cuối ca và số đơn vị quy đổi. Số chưa nhập hiển thị 0. Ô số thùng và số lẻ thay đổi theo bước 1; rượu quy đổi 12 chai/thùng. Cuối ca chỉ lưu khi không còn bàn mở. Số kiểm được giữ ở trạng thái `waiting_sync` cho đến khi hóa đơn ca đồng bộ đủ; lúc đó mới có chênh lệch.

## Đối chiếu theo bàn

Mỗi dòng có bàn, mã món, số gọi hiện có, số bán trên hóa đơn và `returned_cancelled`. Khi không có lịch sử hủy từng dòng, `returned_cancelled` mang trạng thái `unknown` và giao diện hiện “Chưa có dữ liệu”; không hiển thị 0.
