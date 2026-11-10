package com.harlequin.graveborne;

/** One of the four resurrected warriors. */
public final class Member {
    public static final int MELEE = 0, REACH = 1, RANGED = 2;

    public final String name, title, portrait, weapon;
    public final int reach;
    public int hp, maxHp, dmgMin, dmgMax;
    public final float cooldown;
    public float cd;          // seconds until ready
    public float hurtFlash, swing;

    public Member(String name, String title, String portrait, String weapon, int reach, int hp, int dmgMin, int dmgMax, float cooldown) {
        this.name = name; this.title = title; this.portrait = portrait; this.weapon = weapon; this.reach = reach;
        this.hp = this.maxHp = hp; this.dmgMin = dmgMin; this.dmgMax = dmgMax; this.cooldown = cooldown;
    }

    public boolean alive() { return hp > 0; }

    public static Member[] party() {
        return new Member[]{
                new Member("ALDRIC", "KNIGHT", "aldric", "sword", MELEE, 42, 4, 8, 1.1f),
                new Member("BRANN", "BERSERKER", "brann", "axe", MELEE, 46, 6, 11, 1.6f),
                new Member("SERA", "SPEARWARDEN", "sera", "spear", REACH, 34, 4, 7, 1.2f),
                new Member("VESH", "CROSSBOW", "vesh", "xbow", RANGED, 28, 5, 9, 2.0f),
        };
    }
}
