# Ứng dụng Android nhắc món

Ứng dụng này lấy hàng đợi từ máy quản lý qua HTTPS, đọc món mới và món quá hạn bằng Text-to-Speech tiếng Việt. Dịch vụ nền có thông báo thường trực để tiếp tục hoạt động khi nhân viên chuyển sang ứng dụng CUKCUK. Khóa API CUKCUK chỉ ở máy quản lý; máy tính bảng chỉ giữ `RUNNER_DEVICE_KEY`.

## Tạo APK

Máy phát triển cần Android SDK 35, JDK 17 trở lên và Gradle 8.11.1. Mở thư mục này bằng Android Studio rồi chọn **Build > Build APK(s)**. Hoặc chạy `gradle assembleDebug` trong thư mục này khi đã cài SDK/Gradle. APK nằm tại `app/build/outputs/apk/debug/app-debug.apk`. Dự án chưa kèm Gradle wrapper vì môi trường hiện tại chưa có Gradle/Android SDK.

## Chạy thử tại quán

1. Trên máy quản lý, chạy web `app.py` và tiến trình đồng bộ `order_monitor.py` theo README ở thư mục gốc. Máy quản lý và máy tính bảng cùng mạng Wi-Fi. Máy chủ phải có HTTPS với chứng chỉ được Android tin cậy, khớp tên máy trong URL.
2. Cài APK lên máy tính bảng. Nhập URL của máy quản lý, khóa `RUNNER_DEVICE_KEY` và chu kỳ cập nhật từ máy quản lý (mặc định 5 giây, cho phép 2–60 giây), rồi bấm **Bắt đầu đọc món** và **Thử giọng nói**. Có thể đổi chu kỳ này và bấm **Bắt đầu đọc món** lại mà không tạo APK mới.
3. Mở lại CUKCUK để order. Thử gọi một món mới, đợi ứng dụng đọc. Giữ thông báo thường trực của Nhắc món; thử cả khi màn hình CUKCUK ở phía trước. Cho phép thông báo nếu Android hỏi.
4. Nếu không nghe tiếng Việt, cài giọng Text-to-Speech tiếng Việt trên máy tính bảng. Kiểm tra âm lượng phương tiện và cấu hình pin của thiết bị.

Chế độ tự dừng khi KDS hoàn thành phải xác minh `OrderDetails.Status` trên một order thử trước khi bật `RUNNER_COMPLETION_MODE=kds`; xem README gốc. KDS hoàn thành chỉ xác nhận bếp làm xong, không xác nhận món đã được mang đến bàn.
