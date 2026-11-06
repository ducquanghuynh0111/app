# Quy tắc chung cho các tab Kho

## Người thao tác

- Chỉ tài khoản chủ quán hoặc quản lý được nhập và sửa số liệu kho ở mọi tab.
- Mỗi lần sửa số đã lưu cần ghi người thực hiện và thời điểm.

## Ngày kinh doanh

- Dùng ca thu ngân hiện có trong phần mềm làm mốc ca kinh doanh cho các tab kho; không mở ca kho riêng.
- Hàng nhập, hóa đơn và số kiểm sau 0 giờ vẫn thuộc ca thu ngân đã bắt đầu trước 0 giờ, cho đến khi ca đó kết thúc.
- Các báo cáo theo tuần lấy các ca kinh doanh theo ngày bắt đầu ca.

## Dữ liệu chưa đủ

- Số mua, số dùng thực tế, số dùng ước tính và số dùng theo định mức phải có nhãn riêng; không tự coi một số là số khác.
- Thiếu hóa đơn CUKCUK hoặc thiếu định mức món thì hiển thị trạng thái chưa đủ dữ liệu; không mặc định bằng 0 hoặc kết luận thất thoát.

## Cập nhật ngày 2026-11-05: nhập kho theo ngày, không theo ca thu ngân

Quản lý chọn ngày và nhập số ở các mốc đầu/cuối ngày khi có số liệu. Ứng dụng không dùng thao tác mở hoặc khóa ca thu ngân để cho phép nhập hoặc tính kho. Mỗi mặt hàng được lưu riêng; ô trống là chưa nhập, số 0 là đã xác nhận không có hàng. Nút tính kết quả chạy theo dữ liệu hiện có và chỉ kết luận cho mặt hàng đủ dữ liệu. Quy tắc này thay thế các đoạn trước về việc gắn số kiểm kho với ca thu ngân trong mọi đặc tả kho. Chi tiết hàng bán trực tiếp ở specs/007-manual-stock-reconciliation/spec.md.
