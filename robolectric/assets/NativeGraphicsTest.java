package example.robolectric;

import static org.junit.Assert.assertEquals;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 34)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class NativeGraphicsTest {
    @Test
    public void rectanglePaintsOnlyInsideBounds() {
        Bitmap bitmap = Bitmap.createBitmap(4, 4, Bitmap.Config.ARGB_8888);
        try {
            Paint paint = new Paint();
            paint.setColor(Color.RED);
            new Canvas(bitmap).drawRect(1, 1, 3, 3, paint);
            assertEquals(Color.RED, bitmap.getPixel(1, 1));
            assertEquals(Color.TRANSPARENT, bitmap.getPixel(0, 0));
        } finally {
            bitmap.recycle();
        }
    }
}
