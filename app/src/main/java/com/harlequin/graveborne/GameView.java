package com.harlequin.graveborne;

import android.content.Context;
import android.content.res.AssetManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;

/** Runs the game loop on its own thread and scales the 180-wide retro screen up with crisp pixels. */
public class GameView extends SurfaceView implements SurfaceHolder.Callback, Runnable {
    private final Context ctx;
    private Thread thread;
    private volatile boolean running, surfaceReady;
    private Game game;
    private Bitmap frame;
    private final Paint paint = new Paint();
    private final Rect src = new Rect(), dst = new Rect();
    private int scale = 1, offX, offY;
    // hold-to-repeat on the movement pad
    private volatile int heldAction = -1;
    private volatile float heldTime;
    private final Object lock = new Object();

    public GameView(Context c) {
        super(c);
        ctx = c;
        getHolder().addCallback(this);
        setFocusable(true);
        setFocusableInTouchMode(true);
        paint.setFilterBitmap(false);
        paint.setAntiAlias(false);
        paint.setDither(false);
    }

    private final Atlas.Loader loader = new Atlas.Loader() {
        @Override
        public int[] image(String name, int[] size) {
            try (InputStream in = ctx.getAssets().open(name)) {
                BitmapFactory.Options o = new BitmapFactory.Options();
                o.inScaled = false;
                o.inPremultiplied = false;
                o.inPreferredConfig = Bitmap.Config.ARGB_8888;
                Bitmap b = BitmapFactory.decodeStream(in, null, o);
                size[0] = b.getWidth(); size[1] = b.getHeight();
                int[] px = new int[size[0] * size[1]];
                b.getPixels(px, 0, size[0], 0, 0, size[0], size[1]);
                b.recycle();
                return px;
            } catch (Exception e) { throw new RuntimeException(e); }
        }

        @Override
        public String text(String name) {
            try (InputStream in = ctx.getAssets().open(name, AssetManager.ACCESS_STREAMING)) {
                ByteArrayOutputStream bo = new ByteArrayOutputStream();
                byte[] buf = new byte[8192];
                int n;
                while ((n = in.read(buf)) > 0) bo.write(buf, 0, n);
                return bo.toString("UTF-8");
            } catch (Exception e) { throw new RuntimeException(e); }
        }
    };

    @Override
    public void surfaceCreated(SurfaceHolder h) { }

    @Override
    public void surfaceChanged(SurfaceHolder h, int format, int w, int hh) {
        synchronized (lock) {
            scale = Math.max(1, Math.min(w / Game.W, hh / 360));
            int vh = hh / scale;
            if (game == null || game.H != Math.max(360, vh)) {
                game = new Game(loader, vh);
                frame = Bitmap.createBitmap(Game.W, game.H, Bitmap.Config.ARGB_8888);
            }
            offX = (w - Game.W * scale) / 2;
            offY = (hh - game.H * scale) / 2;
            src.set(0, 0, Game.W, game.H);
            dst.set(offX, offY, offX + Game.W * scale, offY + game.H * scale);
            surfaceReady = true;
        }
    }

    @Override
    public void surfaceDestroyed(SurfaceHolder h) { surfaceReady = false; }

    public void resume() {
        running = true;
        thread = new Thread(this, "graveborne-loop");
        thread.start();
    }

    public void pause() {
        running = false;
        try { if (thread != null) thread.join(500); } catch (InterruptedException ignored) { }
    }

    @Override
    public void run() {
        long last = System.nanoTime();
        while (running) {
            long now = System.nanoTime();
            float dt = (now - last) / 1e9f;
            last = now;
            if (!surfaceReady || game == null) { sleep(16); continue; }
            synchronized (lock) {
                if (heldAction >= 0) {
                    heldTime += dt;
                    if (heldTime > 0.32f && game.idle()) game.input(heldAction);
                }
                game.update(dt);
                game.render();
                frame.setPixels(game.g.px, 0, Game.W, 0, 0, Game.W, game.H);
            }
            Canvas c = null;
            try {
                c = getHolder().lockCanvas();
                if (c != null) {
                    c.drawColor(0xff0c0912);
                    c.drawBitmap(frame, src, dst, paint);
                }
            } finally {
                if (c != null) getHolder().unlockCanvasAndPost(c);
            }
            long spent = (System.nanoTime() - now) / 1000000;
            if (spent < 16) sleep(16 - spent);
        }
    }

    private static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException ignored) { }
    }

    @Override
    public boolean onTouchEvent(MotionEvent e) {
        int a = e.getActionMasked();
        if (game == null) return true;
        if (a == MotionEvent.ACTION_DOWN || a == MotionEvent.ACTION_POINTER_DOWN) {
            int i = e.getActionIndex();
            int vx = (int) ((e.getX(i) - offX) / scale), vy = (int) ((e.getY(i) - offY) / scale);
            synchronized (lock) {
                game.tap(vx, vy);
                int pa = game.padAction(vx, vy);
                if (pa == Game.ACT_FWD || pa == Game.ACT_BACK || pa == Game.ACT_LEFT || pa == Game.ACT_RIGHT) {
                    heldAction = pa; heldTime = 0;
                }
            }
        } else if (a == MotionEvent.ACTION_UP || a == MotionEvent.ACTION_CANCEL) {
            heldAction = -1;
        }
        return true;
    }

    @Override
    public boolean onKeyDown(int code, KeyEvent e) {
        if (game == null) return super.onKeyDown(code, e);
        int act;
        switch (code) {
            case KeyEvent.KEYCODE_DPAD_UP: case KeyEvent.KEYCODE_W: act = Game.ACT_FWD; break;
            case KeyEvent.KEYCODE_DPAD_DOWN: case KeyEvent.KEYCODE_S: act = Game.ACT_BACK; break;
            case KeyEvent.KEYCODE_DPAD_LEFT: case KeyEvent.KEYCODE_Q: act = Game.ACT_TURNL; break;
            case KeyEvent.KEYCODE_DPAD_RIGHT: case KeyEvent.KEYCODE_E: act = Game.ACT_TURNR; break;
            case KeyEvent.KEYCODE_A: case KeyEvent.KEYCODE_BUTTON_L1: act = Game.ACT_LEFT; break;
            case KeyEvent.KEYCODE_D: case KeyEvent.KEYCODE_BUTTON_R1: act = Game.ACT_RIGHT; break;
            case KeyEvent.KEYCODE_BUTTON_A: case KeyEvent.KEYCODE_SPACE: case KeyEvent.KEYCODE_ENTER: act = Game.ACT_USE; break;
            case KeyEvent.KEYCODE_BUTTON_Y: case KeyEvent.KEYCODE_M: act = Game.ACT_MAP; break;
            case KeyEvent.KEYCODE_1: act = Game.ACT_ATTACK0; break;
            case KeyEvent.KEYCODE_2: act = Game.ACT_ATTACK0 + 1; break;
            case KeyEvent.KEYCODE_3: act = Game.ACT_ATTACK0 + 2; break;
            case KeyEvent.KEYCODE_4: act = Game.ACT_ATTACK0 + 3; break;
            default: return super.onKeyDown(code, e);
        }
        synchronized (lock) { game.input(act); }
        return true;
    }
}
