package vn.quannhau.nhacmon;

import android.Manifest;
import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

public class MainActivity extends Activity {
    private EditText server;
    private EditText key;
    private EditText pollSeconds;
    private TextView status;
    private TextView queue;
    private final BroadcastReceiver updates = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            status.setText(intent.getStringExtra("status"));
            try {
                JSONArray items = new JSONArray(intent.getStringExtra("items"));
                StringBuilder list = new StringBuilder();
                for (int i = 0; i < items.length(); i++) {
                    JSONObject item = items.getJSONObject(i);
                    String place = item.optString("table_name").isEmpty()
                            ? "Order " + item.optString("order_no") : "Bàn " + item.optString("table_name");
                    list.append(place).append(" · ").append(item.optString("quantity"))
                            .append(" × ").append(item.optString("item_name")).append("\n\n");
                }
                queue.setText(items.length() + " món đang theo dõi\n\n" + list);
            } catch (Exception error) { queue.setText("Không đọc được danh sách món"); }
        }
    };

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(24, 24, 24, 24);
        TextView title = new TextView(this);
        title.setText("Nhắc món CUKCUK"); title.setTextSize(26);
        panel.addView(title);
        server = new EditText(this);
        server.setSingleLine(true);
        server.setHint("https://ten-may-quan-ly:8000");
        server.setInputType(17);
        server.setText(getSharedPreferences(ReminderService.PREFS, MODE_PRIVATE).getString("server", ""));
        panel.addView(server);
        key = new EditText(this);
        key.setSingleLine(true);
        key.setHint("Khóa thiết bị nhắc món");
        key.setInputType(129);
        key.setText(getSharedPreferences(ReminderService.PREFS, MODE_PRIVATE).getString("key", ""));
        panel.addView(key);
        pollSeconds = new EditText(this);
        pollSeconds.setSingleLine(true);
        pollSeconds.setHint("Cập nhật từ máy quản lý mỗi mấy giây (2–60)");
        pollSeconds.setInputType(InputType.TYPE_CLASS_NUMBER);
        pollSeconds.setText(String.valueOf(getSharedPreferences(ReminderService.PREFS, MODE_PRIVATE).getInt("poll_seconds", 5)));
        panel.addView(pollSeconds);
        Button start = button("Bắt đầu đọc món", panel);
        Button test = button("Thử giọng nói", panel);
        Button stop = button("Dừng đọc món", panel);
        status = new TextView(this);
        status.setText("Chưa kết nối"); status.setTextSize(18);
        panel.addView(status);
        queue = new TextView(this);
        queue.setText("Chưa có danh sách món"); queue.setTextSize(18);
        panel.addView(queue);
        ScrollView scroll = new ScrollView(this);
        scroll.addView(panel);
        setContentView(scroll);
        start.setOnClickListener(view -> {
            String url = server.getText().toString().trim().replaceAll("/+$", "");
            String deviceKey = key.getText().toString().trim();
            if (!url.startsWith("https://") || deviceKey.length() < 32) {
                status.setText("Cần URL HTTPS và khóa thiết bị dài ít nhất 32 ký tự");
                return;
            }
            int interval;
            try { interval = Integer.parseInt(pollSeconds.getText().toString().trim()); }
            catch (NumberFormatException error) {
                status.setText("Chu kỳ cập nhật phải là số giây từ 2 đến 60");
                return;
            }
            if (interval < 2 || interval > 60) {
                status.setText("Chu kỳ cập nhật phải từ 2 đến 60 giây");
                return;
            }
            android.content.SharedPreferences prefs = getSharedPreferences(ReminderService.PREFS, MODE_PRIVATE);
            android.content.SharedPreferences.Editor editor = prefs.edit();
            if (!url.equals(prefs.getString("server", ""))) editor.putInt("event_cursor", -1);
            editor.putString("server", url).putString("key", deviceKey).putInt("poll_seconds", interval).apply();
            if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                    != PackageManager.PERMISSION_GRANTED) requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 1);
            startForegroundService(new Intent(this, ReminderService.class));
            status.setText("Đang kết nối. Có thể mở CUKCUK sau khi thấy thông báo thường trực.");
        });
        test.setOnClickListener(view -> startForegroundService(new Intent(this, ReminderService.class).setAction(ReminderService.ACTION_TEST)));
        stop.setOnClickListener(view -> {
            startService(new Intent(this, ReminderService.class).setAction(ReminderService.ACTION_STOP));
            status.setText("Đã dừng đọc món");
        });
    }

    private Button button(String label, LinearLayout parent) {
        Button result = new Button(this);
        result.setText(label);
        parent.addView(result, new LinearLayout.LayoutParams(-1, -2));
        return result;
    }

    @Override public void onStart() {
        super.onStart();
        IntentFilter filter = new IntentFilter(ReminderService.ACTION_UPDATE);
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(updates, filter, Context.RECEIVER_NOT_EXPORTED);
        else registerReceiver(updates, filter);
    }

    @Override public void onStop() {
        unregisterReceiver(updates);
        super.onStop();
    }
}
