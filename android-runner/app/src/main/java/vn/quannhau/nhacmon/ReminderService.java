package vn.quannhau.nhacmon;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.OffsetDateTime;
import java.util.Locale;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

public class ReminderService extends Service {
    public static final String ACTION_UPDATE = "vn.quannhau.nhacmon.UPDATE";
    public static final String ACTION_STOP = "vn.quannhau.nhacmon.STOP";
    public static final String ACTION_TEST = "vn.quannhau.nhacmon.TEST";
    public static final String PREFS = "connection";
    private static final String CHANNEL = "reminders";
    private final Handler main = new Handler(Looper.getMainLooper());
    private ScheduledExecutorService worker;
    private ScheduledFuture<?> polling;
    private int workerInterval = -1;
    private TextToSpeech tts;
    private boolean voiceReady;
    private int cursor = -1;

    @Override public void onCreate() {
        super.onCreate();
        cursor = getSharedPreferences(PREFS, MODE_PRIVATE).getInt("event_cursor", -1);
        NotificationManager manager = getSystemService(NotificationManager.class);
        NotificationChannel channel = new NotificationChannel(CHANNEL, "Đọc và nhắc món", NotificationManager.IMPORTANCE_LOW);
        manager.createNotificationChannel(channel);
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                int language = tts.setLanguage(new Locale("vi", "VN"));
                voiceReady = language != TextToSpeech.LANG_MISSING_DATA && language != TextToSpeech.LANG_NOT_SUPPORTED;
                if (!voiceReady) publish("Chưa cài giọng đọc tiếng Việt", "[]");
            } else publish("Không khởi tạo được giọng đọc", "[]");
        });
    }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent == null ? "" : intent.getAction();
        if (ACTION_STOP.equals(action)) {
            stopSelf();
            return START_NOT_STICKY;
        }
        startForeground(1, notification("Đang kết nối máy quản lý"));
        cursor = getSharedPreferences(PREFS, MODE_PRIVATE).getInt("event_cursor", -1);
        if (ACTION_TEST.equals(action)) {
            speak("Thử giọng nói. Ứng dụng nhắc món đang hoạt động.");
        }
        int selected = getSharedPreferences(PREFS, MODE_PRIVATE).getInt("poll_seconds", 5);
        int interval = Math.max(2, Math.min(60, selected));
        if (worker == null) worker = Executors.newSingleThreadScheduledExecutor();
        if (polling == null || interval != workerInterval) {
            if (polling != null) polling.cancel(false);
            polling = worker.scheduleWithFixedDelay(this::pollSafely, 0, interval, TimeUnit.SECONDS);
            workerInterval = interval;
        }
        return START_NOT_STICKY;
    }

    private Notification notification(String status) {
        Intent launch = new Intent(this, MainActivity.class);
        PendingIntent pending = PendingIntent.getActivity(this, 0, launch,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        return new Notification.Builder(this, CHANNEL)
                .setSmallIcon(android.R.drawable.ic_lock_silent_mode_off)
                .setContentTitle("Nhắc món CUKCUK")
                .setContentText(status).setContentIntent(pending).setOngoing(true).build();
    }

    private void pollSafely() {
        try { poll(); }
        catch (Exception error) {
            Log.w("NhacMon", "Không đồng bộ được hàng đợi", error);
            publish("Mất kết nối máy quản lý: " + error.getClass().getSimpleName(), "[]");
        }
    }

    private void poll() throws Exception {
        SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        String server = prefs.getString("server", "");
        String key = prefs.getString("key", "");
        if (!server.startsWith("https://") || key.length() < 32) {
            publish("Cần cấu hình HTTPS và khóa thiết bị", "[]");
            return;
        }
        HttpURLConnection connection = (HttpURLConnection) new URL(server + "/api/runner/queue?after=" + cursor).openConnection();
        connection.setConnectTimeout(5000);
        connection.setReadTimeout(5000);
        connection.setRequestProperty("X-Runner-Key", key);
        connection.setRequestProperty("Accept", "application/json");
        connection.setUseCaches(false);
        try {
            if (connection.getResponseCode() != 200) throw new IllegalStateException("HTTP " + connection.getResponseCode());
            try (InputStream input = connection.getInputStream(); ByteArrayOutputStream output = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[4096];
                int count;
                while ((count = input.read(buffer)) != -1) {
                    if (output.size() + count > 512000) throw new IllegalStateException("Phản hồi quá lớn");
                    output.write(buffer, 0, count);
                }
                JSONObject response = new JSONObject(output.toString(StandardCharsets.UTF_8.name()));
                JSONArray events = response.getJSONArray("events");
                if (cursor > response.getInt("latest_event_id")) cursor = -1;
                if (cursor == -1) cursor = response.getInt("latest_event_id");
                else for (int i = 0; i < events.length(); i++) {
                    JSONObject event = events.getJSONObject(i);
                    cursor = Math.max(cursor, event.getInt("id"));
                    String kind = event.optString("kind");
                    String place = event.optString("table_name").isEmpty()
                            ? "Order " + event.optString("order_no") : "Bàn " + event.optString("table_name");
                    String amount = event.optString("quantity") + " phần " + event.optString("item_name");
                    String dish = place + ", " + amount;
                    if ("late".equals(kind)) speak("Nhắc món quá hạn. " + dish + ". Vui lòng kiểm tra bếp.");
                    else if ("total".equals(kind)) {
                        String added = event.isNull("added_quantity") ? "" : event.optString("added_quantity", "");
                        String prefix = added.isEmpty() || added.equals(event.optString("quantity")) ? ""
                                : "Có thêm " + added + " phần " + event.optString("item_name") + ". ";
                        speak(prefix + "Tổng chưa ra " + amount + ".");
                    }
                    else if ("ready".equals(kind)) {
                        String remaining = event.isNull("remaining_text") ? "" : event.optString("remaining_text", "");
                        speak("Đã ra " + amount + "." + (remaining.isEmpty() ? "" : " " + remaining + "."));
                    }
                    else if ("added".equals(kind)) speak("Bổ sung món. " + place + ", thêm " + amount + ".");
                    else if ("reduced".equals(kind)) speak("Món thay đổi. " + place + ", còn " + amount + ".");
                    else if ("new".equals(kind) || "updated".equals(kind)) speak("Có món mới. " + dish);
                }
                prefs.edit().putInt("event_cursor", cursor).apply();
                JSONObject monitor = response.optJSONObject("monitor");
                String status = "Chờ đồng bộ CUKCUK";
                if (monitor != null) {
                    status = monitor.isNull("last_error") ? "" : monitor.optString("last_error", "");
                    if (status.isEmpty()) {
                        String lastSuccess = monitor.optString("last_success_at", "");
                        try {
                            long age = Duration.between(OffsetDateTime.parse(lastSuccess), OffsetDateTime.now()).getSeconds();
                            status = age > 120 ? "Đồng bộ CUKCUK đã dừng hơn 2 phút" : "Đang theo dõi order";
                        } catch (Exception ignored) { status = "Chờ đồng bộ CUKCUK"; }
                    }
                }
                publish(status, response.getJSONArray("items").toString());
            }
        } finally { connection.disconnect(); }
    }

    private void speak(String message) {
        main.post(() -> { if (voiceReady && tts != null)
            tts.speak(message, TextToSpeech.QUEUE_ADD, null, "dish-" + System.nanoTime()); });
    }

    private void publish(String status, String items) {
        main.post(() -> {
            Intent update = new Intent(ACTION_UPDATE).setPackage(getPackageName());
            update.putExtra("status", status);
            update.putExtra("items", items);
            sendBroadcast(update);
            getSystemService(NotificationManager.class).notify(1, notification(status));
        });
    }

    @Override public void onDestroy() {
        if (worker != null) worker.shutdownNow();
        if (tts != null) { tts.stop(); tts.shutdown(); }
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
