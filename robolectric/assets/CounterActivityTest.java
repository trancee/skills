package example.robolectric;

import static org.junit.Assert.assertEquals;
import static org.robolectric.Shadows.shadowOf;

import android.os.Build;
import android.os.Looper;
import android.widget.Button;
import java.time.Duration;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.LooperMode;
import org.robolectric.android.controller.ActivityController;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = {Build.VERSION_CODES.TIRAMISU, Build.VERSION_CODES.UPSIDE_DOWN_CAKE})
@LooperMode(LooperMode.Mode.PAUSED)
public class CounterActivityTest {
    @Test
    public void clickUpdatesLabelOnlyAtDeadline() {
        try (ActivityController<CounterActivity> controller =
                Robolectric.buildActivity(CounterActivity.class)) {
            controller.setup();
            Button button = controller.get().findViewById(R.id.counter);
            assertEquals("Tap", button.getText().toString());

            button.performClick();
            shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(999));
            assertEquals("Tap", button.getText().toString());
            shadowOf(Looper.getMainLooper()).idleFor(Duration.ofMillis(1));
            assertEquals("Count: 1", button.getText().toString());
        }
    }

    @Test
    public void recreationPreservesClickedCount() {
        try (ActivityController<CounterActivity> controller =
                Robolectric.buildActivity(CounterActivity.class)) {
            controller.setup();
            controller.get().findViewById(R.id.counter).performClick();
            controller.recreate();

            Button button = controller.get().findViewById(R.id.counter);
            assertEquals("Count: 1", button.getText().toString());
        }
    }

    @Test
    @Config(qualifiers = "fr-rFR")
    public void localeSelectsFrenchResource() {
        try (ActivityController<CounterActivity> controller =
                Robolectric.buildActivity(CounterActivity.class)) {
            controller.setup();
            Button button = controller.get().findViewById(R.id.counter);
            assertEquals("Appuyer", button.getText().toString());
        }
    }
}
