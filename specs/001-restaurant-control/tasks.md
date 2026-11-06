# Tác vụ triển khai

- [x] T020 Khóa ba tab chưa hoàn thiện ở thanh điều hướng, chặn mở bằng mã giao diện và giữ lối vào Quy trình cho nhân viên.
- [x] T021 Tạo schema.sql không có dữ liệu và caidat.py nhập cấu trúc SQLite, chạy ứng dụng, không ghi đè cơ sở dữ liệu cũ.
- [x] T022 Rút gọn tên tab bị khóa và cho thanh điều hướng tự xuống dòng thay vì cuộn ngang.
## Nền tảng

- [x] T001 Tạo đặc tả và kế hoạch cho ứng dụng kiểm soát vận hành.
- [x] T002 Tạo SQLite schema, tài khoản chủ quán và đăng nhập có phiên.
- [x] T003 Tạo giao diện responsive và phân quyền máy chủ.

## US1 — Đối soát doanh thu

- [x] T004 Tạo ca tiền, nhập số liệu CUKCUK và thu chi có chứng từ.
- [x] T005 Tính tiền kỳ vọng, chênh lệch và khóa ca có lý do.

## US2 — Kho

- [x] T006 Tạo danh mục và sổ nhập/xuất.
- [x] T007 Tạo kiểm kê và duyệt chênh lệch.
- [x] T008 Tạo cảnh báo dưới tồn tối thiểu.

## US3 — Bán ra

- [x] T009 Nhập CSV bán hàng có chống trùng và trừ kho hàng trực tiếp.
- [x] T010 Xuất báo cáo ca và kho.

## US4 — Nhân viên

- [x] T011 Tạo lịch ca, chấm vào/ra và báo đi muộn.
- [x] T012 Ghi nhận lỗi order và trạng thái xử lý.

## Xác minh

- [x] T013 Kiểm thử phép tính tiền, kiểm kê và phân quyền.
- [x] T014 Viết hướng dẫn vận hành và cập nhật chỉ mục thư mục Spec Kit.

## Việc chờ dữ liệu và quyết định của quán

- [ ] T015 Ánh xạ Bảng kê hóa đơn và báo cáo doanh thu CUKCUK từ file xuất thực tế, bao gồm phương thức thanh toán.
- [ ] T016 Chọn mức theo dõi bàn giao món: chỉ ghi ngoại lệ hoặc xác nhận từng món; triển khai theo quyết định.
- [ ] T017 Đối chiếu báo cáo món gửi bếp/chế biến/trả lại với sự cố order sau khi có mẫu báo cáo.
