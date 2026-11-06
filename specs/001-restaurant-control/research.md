# Nghiên cứu và giả định

Tài liệu CUKCUK cho thấy phần mềm đã có phân hệ định lượng nguyên vật liệu, kiểm kê kho và chấm công. Vì vậy ứng dụng này ưu tiên lớp đối soát, bằng chứng kiểm kê và ngoại lệ vận hành. Phạm vi CUKCUK đang dùng tại quán và khả năng xuất CSV/API chưa được xác nhận.

Ảnh hóa đơn mẫu chứa số hóa đơn/order, bàn, người phục vụ, người thu ngân, các dòng món và tổng tiền. Ảnh không xác nhận phương thức thanh toán thực nhận hoặc món đã được bưng. Không dùng ảnh đơn lẻ làm bằng chứng đối soát tiền hay năng suất nhân viên.

Nguồn chính thức:

- Định lượng nguyên vật liệu: https://helpv2.cukcuk.vn/vi/kb/thuc-hien-dinh-luong-nvl-cho-mon-va-xuat-kho-nvl-tuong-ung
- Kiểm kê kho: https://helpv2.cukcuk.vn/vi/kb/1010200_kiem_ke_kho
- Chấm công: https://helpv2.cukcuk.vn/vi/kb/ghi-nhan-so-gio-cong-theo-gio-ra-gio-vao-thuc-te-cua-nhan-vien-de-tinh-luong-chinh-xac
- Bảng kê hóa đơn và hình thức thanh toán: https://helpv2.cukcuk.vn/vi/kb/huong-dan-thiet-lap-cho-phep-quan-ly-nha-hang-biet-duoc-hinh-thuc-thanh-toan-chi-tiet-tren-hoa-don
- Báo cáo bán hàng xuất Excel: https://helpv2.cukcuk.vn/vi/kb/1050000_tinh_hinh_ban_hang
- Theo dõi số món chế biến, trả lại: https://helpv2.cukcuk.vn/vi/kb/theo_doi_so_luong_mon_che_bien__tra_lai

Các giả định cần xác nhận được ghi trong spec.md. Khi có mẫu CSV, cần kiểm tra định dạng tiền, mã bill, hủy/trả, ngày ca và phương thức thanh toán trước khi ánh xạ.
