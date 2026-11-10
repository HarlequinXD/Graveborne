package com.harlequin.graveborne;

import android.content.Context;
import android.content.res.AssetFileDescriptor;
import android.media.AudioAttributes;
import android.media.MediaPlayer;
import android.media.SoundPool;

import java.util.HashMap;
import java.util.Random;

/** SoundPool for effects, a looping MediaPlayer for the score. */
public final class AndroidAudio implements Audio {
    private final Context ctx;
    private final SoundPool pool;
    private final HashMap<String, Integer> ids = new HashMap<>();
    private final Random rnd = new Random();
    private MediaPlayer player;
    private String current;
    private boolean paused;
    private static final float MUSIC_VOL = 0.5f, SFX_VOL = 0.9f;

    public AndroidAudio(Context c) {
        ctx = c.getApplicationContext();
        AudioAttributes attrs = new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_GAME)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
        pool = new SoundPool.Builder().setMaxStreams(14).setAudioAttributes(attrs).build();
        try {
            String[] files = ctx.getAssets().list("sfx");
            if (files != null) {
                for (String f : files) {
                    if (!f.endsWith(".ogg")) continue;
                    AssetFileDescriptor fd = ctx.getAssets().openFd("sfx/" + f);
                    ids.put(f.substring(0, f.length() - 4), pool.load(fd, 1));
                    fd.close();
                }
            }
        } catch (Exception ignored) { }
    }

    @Override
    public synchronized void sfx(String name) {
        Integer id = ids.get(name);
        if (id == null || paused) return;
        boolean vary = name.startsWith("step") || name.startsWith("hit") || name.startsWith("hurt") || name.equals("swing")
                || name.equals("ouch") || name.startsWith("atk");
        float rate = vary ? 0.92f + rnd.nextFloat() * 0.16f : 1f;
        float v = name.startsWith("step") ? SFX_VOL * 0.55f : name.equals("turn") ? SFX_VOL * 0.5f : SFX_VOL;
        pool.play(id, v, v, 1, 0, rate);
    }

    @Override
    public synchronized void music(String track) {
        if (track == null ? current == null : track.equals(current)) return;
        current = track;
        stopPlayer();
        if (track == null) return;
        try {
            AssetFileDescriptor fd = ctx.getAssets().openFd("music/" + track + ".ogg");
            MediaPlayer mp = new MediaPlayer();
            mp.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());
            mp.setDataSource(fd.getFileDescriptor(), fd.getStartOffset(), fd.getLength());
            fd.close();
            mp.setLooping(!track.equals("death"));
            mp.setVolume(MUSIC_VOL, MUSIC_VOL);
            mp.prepare();
            if (!paused) mp.start();
            player = mp;
        } catch (Exception ignored) { player = null; }
    }

    private void stopPlayer() {
        if (player != null) {
            try { player.stop(); } catch (Exception ignored) { }
            player.release();
            player = null;
        }
    }

    public synchronized void pause() {
        paused = true;
        if (player != null) try { player.pause(); } catch (Exception ignored) { }
        pool.autoPause();
    }

    public synchronized void resume() {
        paused = false;
        if (player != null) try { player.start(); } catch (Exception ignored) { }
        pool.autoResume();
    }
}
