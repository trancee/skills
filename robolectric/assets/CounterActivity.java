package example.robolectric;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.Button;

public final class CounterActivity extends Activity {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private int count;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        count = state == null ? 0 : state.getInt("count");
        setContentView(R.layout.counter);
        Button button = findViewById(R.id.counter);
        if (count > 0) button.setText(getString(R.string.count, count));
        button.setOnClickListener(view -> {
            count++;
            handler.postDelayed(() -> button.setText(getString(R.string.count, count)), 1000);
        });
    }

    @Override
    protected void onSaveInstanceState(Bundle state) {
        state.putInt("count", count);
        super.onSaveInstanceState(state);
    }

    @Override
    protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }
}
