package com.harlequin.graveborne;

/** A cursed creature that walks the grid toward the party and attacks when adjacent. */
public final class Monster {
    public final String type;
    public int x, y;          // current cell (destination while moving)
    public int fromX, fromY;  // previous cell, for smooth sliding
    public float moveT = 1f;  // 0..1 progress of the slide
    public int hp, maxHp, dmgMin, dmgMax, xp;
    public float moveEvery, attackEvery, evade;
    public float moveCd, attackCd;
    public float attackAnim, hitFlash, idleT;
    public boolean awake;
    public final String label;

    public Monster(String type, int x, int y) {
        this.type = type; this.x = this.fromX = x; this.y = this.fromY = y;
        switch (type) {
            case "ghoul": maxHp = 24; dmgMin = 4; dmgMax = 8; moveEvery = 0.75f; attackEvery = 1.4f; xp = 14; label = "GHOUL"; break;
            case "wraith": maxHp = 30; dmgMin = 5; dmgMax = 9; moveEvery = 1.2f; attackEvery = 1.8f; xp = 20; evade = 0.25f; label = "WRAITH"; break;
            default: maxHp = 18; dmgMin = 3; dmgMax = 6; moveEvery = 1.0f; attackEvery = 1.6f; xp = 10; label = "SKELETON"; break;
        }
        hp = maxHp;
        idleT = (x * 7 + y * 13) % 10 * 0.1f;
        moveCd = moveEvery;
        attackCd = attackEvery * 0.6f;
    }

    public boolean alive() { return hp > 0; }

    public float wx() { return fromX + (x - fromX) * moveT; }
    public float wy() { return fromY + (y - fromY) * moveT; }

    public String frame() {
        if (attackAnim > 0) return "attack";
        return ((int) (idleT * 1.6f) & 1) == 0 ? "idle" : "idle2";
    }
}
