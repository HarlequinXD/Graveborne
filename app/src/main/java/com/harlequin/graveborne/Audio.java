package com.harlequin.graveborne;

/** Sound hooks. The Android build plays OGG files from assets/sfx and assets/music. */
public interface Audio {
    void sfx(String name);

    /** Switch the looping score (null = silence). Same name again is ignored. */
    void music(String track);

    Audio NONE = new Audio() {
        public void sfx(String name) { }
        public void music(String track) { }
    };
}
