# Kế hoạch triển khai: Kiểm kê hàng bán trực tiếp

## Bổ sung: quy đổi số bán ở bảng tồn kho

1. Đọc đơn vị bán của từng dòng hóa đơn đã đồng bộ, áp quy cách của mặt hàng để đổi thùng/cây thành lon/chai/gói trước khi cộng số bán.
2. Nếu đơn vị không rõ, để trống số bán và phép tính chênh lệch cho mặt hàng đó; hiển thị thông báo cần kiểm tra dữ liệu.
3. Kiểm thử hóa đơn bán theo thùng và trường hợp thiếu đơn vị; giữ màu cảnh báo theo ngưỡng 0, 24, trên 24.

## Bổ sung: tab kho chưa hoàn thiện

Giữ tab hàng bán trực tiếp hoạt động; vô hiệu hóa ba tab kho còn lại, giữ nhãn ngắn và cho thanh tab tự xuống dòng.

## Bổ sung: giao diện và kiểm tra tên trùng

1. Dùng chung hệ màu cho năm nhóm ở bảng kiểm và báo cáo ngày; tạo tiêu đề và khoảng cách rõ cho ba mục chính.
2. Đọc danh mục CUKCUK qua API hiện có, chuẩn hóa tên và liệt kê toàn bộ nhóm trùng với mã tương ứng; không thay đổi danh mục CUKCUK.

## Bổ sung: nhập lẻ đầu ngày và hợp nhất mã hiển thị

1. Cho nhập và lưu số đơn vị lẻ ở đầu ngày bằng cùng kiểm tra quy cách như cuối ngày.
2. Khai mã chính và bí danh của ba cặp đã nêu cùng hai cặp Huda đã xác nhận; ẩn dòng mã cũ khi gieo danh mục mà không xóa lịch sử.
3. Quy mã CUKCUK về mã chính khi tính bàn mở, hóa đơn sau ca, tồn bán và lịch sử ngày; kiểm thử số lượng không bị tách đôi.

**Branch**: `002-saleable-inventory` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Summary

Hoàn thiện tính năng đang có bằng cách ánh xạ BATR vào bánh tráng và cả DAUPHONG, DAPH vào đậu phộng; chỉ bia làm bàn hết cảnh báo đỏ. Kiểm hàng theo ca thu ngân, kể cả ca qua 0 giờ. Chỉ cho kiểm cuối ca sau khi mọi bàn đóng; cuối ca nhập thùng nguyên và chai/lon lẻ. Có thể lưu số kiểm trước khi hóa đơn đồng bộ đủ, nhưng chỉ tính chênh lệch sau khi dữ liệu đủ. Chỉ chủ quán/quản lý được nhập và sửa; giữ nhật ký. Rượu quy đổi 12 chai/thùng.

## Technical Context

**Language/Version**: Python 3 hiện dùng trong dự án; JavaScript trình duyệt  
**Primary Dependencies**: Python standard library, giao diện HTML/CSS/JavaScript hiện có  
**Storage**: SQLite hiện có; dữ liệu vận hành không ghi trong mã nguồn  
**Testing**: `python -m unittest discover -s tests -q`, `node --check static/app.js`  
**Target Platform**: Máy quản lý chạy máy chủ nội bộ; trình duyệt trên máy tính và điện thoại  
**Project Type**: Web app nội bộ bổ sung CUKCUK  
**Performance Goals**: Mở tối đa 100 bàn đang gọi mà không yêu cầu mở từng hóa đơn thủ công  
**Constraints**: Chỉ gọi API CUKCUK lúc người dùng tải bảng hoặc khi xác nhận đóng bàn/đồng bộ ca; giữ bộ đệm danh mục; không suy đoán lượng trả/hủy từng món; không sửa ca cũ đã khóa  
**Scale/Scope**: Một chi nhánh, 42 mặt hàng hiện theo dõi, tối đa 200 order mở trong một lượt theo giới hạn hiện tại

## Constitution Check

`.specify/memory/constitution.md` hiện là bản mẫu chưa có nguyên tắc đã phê chuẩn. Kế hoạch tuân theo các ràng buộc đã xác nhận trong đặc tả: CUKCUK là nguồn order/hóa đơn, không sửa dữ liệu CUKCUK, lưu dấu thay đổi, không quy lỗi nhân viên từ chênh lệch đơn lẻ. Không có cổng nguyên tắc bổ sung để đánh giá.

## Project Structure

### Documentation (this feature)

- `specs/002-saleable-inventory/spec.md`: yêu cầu đã làm rõ.
- `specs/002-saleable-inventory/research.md`: nguồn và quyết định về dữ liệu CUKCUK.
- `specs/002-saleable-inventory/data-model.md`: thực thể, ánh xạ và quy tắc dữ liệu.
- `specs/002-saleable-inventory/contracts/`: hợp đồng dữ liệu cho màn bàn và đối chiếu.
- `specs/002-saleable-inventory/quickstart.md`: kịch bản kiểm tra.
- `specs/002-saleable-inventory/tasks.md`: công việc còn thiếu, đánh dấu phần đã có.

### Source Code (repository root)

- `app.py`: API bàn, kiểm kê, báo cáo và phân quyền.
- `table_merchandise.py`: tổng hợp hàng theo bàn từ order đang mở.
- `cukcuk_sync.py`: đọc danh mục, order và hóa đơn từ CUKCUK.
- `menu_catalog.py`, `seed_menu_catalog.py`: danh mục mặt hàng và quy cách.
- `static/index.html`, `static/app.js`, `static/style.css`: màn hình quản lý.
- `tests/`: kiểm tra quy tắc tổng hợp, kiểm kê và quyền sửa.

**Structure Decision**: Mở rộng ứng dụng hiện có và thêm kiểm thử tập trung; không tạo ứng dụng hay cơ sở dữ liệu mới.

## Phase 0 — Research

Đối chiếu [Orders detail](https://graphapi.cukcuk.vn/document/api/orders_detail.html) và [SAInvoice detail](https://graphapi.cukcuk.vn/document/api/sainvoices_detail.html) với dữ liệu hiện được đọc. Quyết định về mã món, đơn ghép bàn và giới hạn trả/hủy được ghi tại [research.md](research.md).

## Phase 1 — Design & Contracts

Mô hình hóa mã gốc và nhóm kiểm kê trong [data-model.md](data-model.md). Định nghĩa trạng thái “chưa xác định” và “chưa có dữ liệu” trong [contracts](contracts/). Dùng [quickstart.md](quickstart.md) để kiểm tra từng kịch bản với dữ liệu giả lập, tránh phụ thuộc tài khoản quán khi thử.

## Implementation Order

1. Ánh xạ ba mã món và bảo đảm chúng có trong danh mục đang hoạt động.
2. Tính số lượng bánh tráng và đậu phộng theo bàn, giữ mã gốc; phân biệt thiếu thực sự với chưa ánh xạ.
3. Hiển thị số bán theo bàn và trả/hủy “Chưa có dữ liệu” khi nguồn không có lịch sử dòng.
4. Đổi cảnh báo bàn sang tiêu chí phải có bia; rượu/nước không xóa cảnh báo đỏ.
5. Gắn lượt nhập và kiểm vào ca thu ngân; kiểm trạng thái mọi bàn trước khi lưu số kiểm cuối ca.
6. Hỗ trợ số thùng nguyên cộng chai/lon lẻ; lưu số kiểm khi đồng bộ thiếu nhưng hoãn tính chênh lệch.
7. Giới hạn nhập/sửa cho chủ quán và quản lý, cập nhật giao diện và kịch bản kiểm tra.

## Post-design Constitution Check

Không thêm dữ liệu cá nhân vào bản đặc tả, hợp đồng hay kiểm thử. Hợp đồng trả/hủy không biểu diễn giá trị 0 khi nguồn chưa cung cấp lịch sử. Không sửa order hoặc hóa đơn trên CUKCUK.
