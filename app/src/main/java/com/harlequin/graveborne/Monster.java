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
    public String label;
    public String[] lines;
    public int lineIdx;
    public boolean npc() { return lines != null; }
    /** Chapter bosses: named, tougher, shown with a health bar. */
    public boolean boss;
    /** Sound set to borrow (bosses reuse the base monsters' voices). */
    public String snd;
    /** Bosses that raise the dead: what they summon, how often. */
    public String summon;
    public float summonEvery, summonCd;
    public String summonVerb = "RAISES THE DEAD";
    /** Siege wave this monster belongs to (0 = present from the start). */
    public int wave;
    /** Raised by a boss mid-fight (falls when the boss does). */
    public boolean summoned;

    public Monster(String type, int x, int y) {
        this.type = type; this.x = this.fromX = x; this.y = this.fromY = y;
        switch (type) {
            case "ghoul": maxHp = 24; dmgMin = 4; dmgMax = 8; moveEvery = 0.75f; attackEvery = 1.4f; xp = 14; label = "GHOUL"; break;
            case "wraith": maxHp = 30; dmgMin = 5; dmgMax = 9; moveEvery = 1.2f; attackEvery = 1.8f; xp = 20; evade = 0.25f; label = "WRAITH"; break;
            case "hound": maxHp = 20; dmgMin = 4; dmgMax = 7; moveEvery = 0.55f; attackEvery = 1.1f; xp = 14; evade = 0.1f; label = "CURSE HOUND"; break;
            // ---- chapter bosses
            case "sexton": boss(150, 6, 11, 1.1f, 1.7f, 120, "THE SEXTON", "skeleton"); summon("skeleton", 9, "RINGS HIS BELL. THE DEAD ANSWER"); break;
            case "captain": boss(190, 7, 13, 0.9f, 1.5f, 160, "THE HANGED CAPTAIN", "skeleton"); summon("skeleton", 11, "CALLS DOWN HIS HANGED MEN"); evade = 0.12f; break;
            case "drowned": boss(240, 8, 14, 1.1f, 1.8f, 200, "THE DROWNED KNIGHT", "ghoul"); summon("ghoul", 12, "DRAGS A DROWNED ONE FROM THE WATER"); break;
            case "colossus": boss(320, 10, 17, 1.4f, 2.2f, 260, "THE BONE COLOSSUS", "skeleton"); summon("skeleton", 10, "SHEDS A SKELETON FROM ITS BONES"); break;
            case "abbot": boss(280, 9, 15, 1.0f, 1.6f, 300, "THE LAST ABBOT", "wraith"); summon("wraith", 13, "SPEAKS A FORBIDDEN PSALM"); evade = 0.2f; break;
            case "hrodmar": boss(400, 11, 19, 1.0f, 1.7f, 380, "KING HRODMAR", "skeleton"); summon("skeleton", 10, "SUMMONS HIS HONOUR GUARD"); break;
            case "heart": boss(500, 10, 18, 99f, 1.5f, 0, "THE HEART OF THE WOUND", "wraith"); summon("wraith", 8, "BEATS. SPIRITS TEAR FREE OF IT"); break;
            case "townsman": maxHp = 99; label = "TOWNSMAN"; break;
            case "priest": maxHp = 99; label = "PRIEST"; break;
            case "guard": maxHp = 99; label = "GUARD"; break;
            case "innkeeper": maxHp = 99; label = "INNKEEPER"; break;
            default: maxHp = 18; dmgMin = 3; dmgMax = 6; moveEvery = 1.0f; attackEvery = 1.6f; xp = 10; label = "SKELETON"; break;
        }
        if (snd == null) snd = type;
        hp = maxHp;
        idleT = (x * 7 + y * 13) % 10 * 0.1f;
        moveCd = moveEvery;
        attackCd = attackEvery * 0.6f;
    }

    private void boss(int hp, int d0, int d1, float move, float atk, int xp, String label, String snd) {
        boss = true; maxHp = hp; dmgMin = d0; dmgMax = d1; moveEvery = move; attackEvery = atk; this.xp = xp; this.label = label; this.snd = snd;
    }

    private void summon(String t, float every, String verb) { summon = t; summonEvery = every; summonCd = every * 0.6f; summonVerb = verb; }

    public boolean alive() { return hp > 0; }

    public float wx() { return fromX + (x - fromX) * moveT; }
    public float wy() { return fromY + (y - fromY) * moveT; }

    public String frame() {
        if (attackAnim > 0 && !npc()) return "attack";
        return ((int) (idleT * 1.6f) & 1) == 0 ? "idle" : "idle2";
    }
}
