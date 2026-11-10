package com.harlequin.graveborne;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Random;

/**
 * Graveborne: the whole game, platform independent. Renders a portrait 180 x H
 * retro screen into an ARGB framebuffer; the platform scales it up crisp and
 * feeds taps in screen coordinates.
 */
public final class Game {
    public static final int W = 180;
    public final int H;
    public final Gfx g;
    private final Atlas atlas;
    private final Atlas.Loader loader;
    private final ViewRenderer vr, vr2;
    private final Random rnd = new Random(1993);

    // ---- state
    public static final int TITLE = 0, PLAY = 1, DEAD = 2, WIN = 3;
    public int state = TITLE;
    public Level lv;
    public int px, py, dir;
    public Member[] party;
    public int keys, potions, xp, plevel = 1;
    private float time, stateT;
    private boolean showMap;
    private int cpX, cpY, cpDir;

    // ---- movement animation
    private static final int A_NONE = 0, A_FWD = 1, A_BACK = 2, A_STRAFE = 3, A_TURN = 4, A_BUMP = 5;
    private int anim = A_NONE, animSide, toX, toY, fromDir;
    private float animT;
    private static final float STEP_TIME = 0.24f, TURN_TIME = 0.22f;
    private final ArrayDeque<Integer> queue = new ArrayDeque<>();

    // ---- effects
    private float shake;
    private float bannerT;
    private final ArrayList<Msg> log = new ArrayList<>();
    private final ArrayList<Floater> floaters = new ArrayList<>();
    private float secretT = -1;
    private int secretX = -1, secretY = -1;
    private float idleHintT;
    private int hintsGiven;
    private boolean switchPressed;

    private static final class Msg {
        final String s; final int c; float age;
        Msg(String s, int c) { this.s = s; this.c = c; }
    }

    private static final class Floater {
        final String s; final int c; float x, y, t;
        Floater(String s, int c, float x, float y) { this.s = s; this.c = c; this.x = x; this.y = y; }
    }

    // ---- layout (virtual pixels)
    private static final int VX = 26, VY = 10;              // 128x128 view
    private final int logY, partyY, padY;
    private static final int PANEL_W = 86, PANEL_H = 54;
    private static final int BTN = 32, BTN_GAP = 4;

    // actions
    public static final int ACT_FWD = 0, ACT_BACK = 1, ACT_LEFT = 2, ACT_RIGHT = 3, ACT_TURNL = 4, ACT_TURNR = 5,
            ACT_USE = 6, ACT_MAP = 7, ACT_POTION = 8, ACT_ATTACK0 = 10;

    public Game(Atlas.Loader loader, int h) {
        this.loader = loader;
        this.H = Math.max(360, h);
        this.g = new Gfx(W, H);
        this.atlas = new Atlas(loader);
        this.vr = new ViewRenderer(atlas);
        this.vr2 = new ViewRenderer(atlas);
        padY = H - 2 * BTN - BTN_GAP - 8;
        partyY = Math.min(padY - 2 * PANEL_H - 10, 196);
        logY = 146;
        newGame();
        state = TITLE;
    }

    public void newGame() {
        lv = Level.parse(loader.text("level1.txt"));
        px = cpX = lv.startX; py = cpY = lv.startY; dir = cpDir = lv.startDir;
        party = Member.party();
        keys = 0; potions = 1; xp = 0; plevel = 1;
        log.clear(); floaters.clear(); queue.clear();
        anim = A_NONE; secretT = -1; switchPressed = false; hintsGiven = 0; idleHintT = 0; showMap = false;
        for (int y = 0; y < lv.h; y++) for (int x = 0; x < lv.w; x++) if (lv.cell[y][x] == Level.SECRET) { secretX = x; secretY = y; }
        say("YOU WAKE ON COLD STONE.", Pal.BONE);
        say("NO HEART BEATS IN YOUR CHESTS.", Pal.STONE7);
        say("THE CURSE HAS RAISED YOU AGAIN.", Pal.CURSE_L);
        bannerT = 3.0f;
        markSeen();
    }

    private void say(String s, int c) {
        // wrap to the log width
        int max = 27;
        while (s.length() > max) {
            int cut = s.lastIndexOf(' ', max);
            if (cut <= 0) cut = max;
            log.add(new Msg(s.substring(0, cut), c));
            s = s.substring(cut).trim();
        }
        log.add(new Msg(s, c));
        while (log.size() > 5) log.remove(0);
    }

    // =================================================================== update
    public void update(float dt) {
        dt = Math.min(dt, 0.1f);
        time += dt; stateT += dt;
        if (shake > 0) shake = Math.max(0, shake - dt);
        if (bannerT > 0) bannerT -= dt;
        for (int i = floaters.size() - 1; i >= 0; i--) {
            Floater f = floaters.get(i);
            f.t += dt; f.y -= dt * 14;
            if (f.t > 0.9f) floaters.remove(i);
        }
        if (state != PLAY) return;
        updateAnim(dt);
        updateSecret(dt);
        updateDoors(dt);
        updateParty(dt);
        updateMonsters(dt);
        if (!switchPressed) {
            idleHintT += dt;
            if (hintsGiven == 0 && idleHintT > 35) { say("A COLD DRAFT SEEPS FROM THE WALL BEHIND YOU...", Pal.TEAL_L); hintsGiven = 1; }
            if (hintsGiven == 1 && idleHintT > 75) { say("ONE BRICK IN THE BACK WALL IS WORN SMOOTH BY HANDS.", Pal.TEAL_L); hintsGiven = 2; }
        }
    }

    private void updateAnim(float dt) {
        if (anim == A_NONE) {
            if (!queue.isEmpty()) act(queue.poll());
            return;
        }
        float dur = anim == A_TURN ? TURN_TIME : anim == A_BUMP ? 0.16f : STEP_TIME;
        animT += dt / dur;
        if (animT >= 1) {
            if (anim == A_FWD || anim == A_BACK || anim == A_STRAFE) {
                px = toX; py = toY;
                arrive();
            }
            anim = A_NONE; animT = 0;
            markSeen();
            if (!queue.isEmpty()) act(queue.poll());
        }
    }

    private void arrive() {
        Item it = lv.itemAt(px, py);
        if (it != null && it.pickable()) {
            lv.items.remove(it);
            if (it.type.equals("key")) { keys++; say("YOU TAKE AN IRON KEY.", Pal.GOLD); }
            else if (it.type.equals("potion")) { potions++; say("YOU TAKE A VIAL OF GRAVE BLOOD.", Pal.RED_L); }
        }
    }

    private void updateSecret(float dt) {
        if (secretT < 0) return;
        float prev = secretT;
        secretT += dt;
        float[] at = {0.5f, 1.2f, 1.9f, 2.6f};
        for (int s = 0; s < 4; s++) {
            if (prev < at[s] && secretT >= at[s]) {
                shake = Math.max(shake, s == 3 ? 0.5f : 0.35f);
                int bedDir = bedFaceDir();
                if (s < 3) {
                    lv.setDeco(secretX, secretY, bedDir, "bed" + (s + 1));
                    if (s == 0) say("STONE GRINDS " + relWhere(secretX, secretY) + "...", Pal.STONE8);
                } else {
                    lv.setDeco(secretX, secretY, bedDir, null);
                    lv.cell[secretY][secretX] = Level.FLOOR;
                    say("THE BED SLAB HAS SUNK. A PASSAGE YAWNS OPEN.", Pal.TEAL_L);
                    secretT = -1;
                    markSeen();
                }
            }
        }
    }

    private int bedFaceDir() {
        for (int d = 0; d < 4; d++) {
            String k = lv.deco(secretX, secretY, d);
            if (k != null && k.startsWith("bed")) return d;
        }
        return Level.W;
    }

    /** "TO YOUR LEFT", "BEHIND YOU"... for a cell relative to the party's facing. */
    private String relWhere(int x, int y) {
        int dx = x - px, dy = y - py;
        int f = dx * Level.DX[dir] + dy * Level.DY[dir];
        int r = dx * Level.DX[(dir + 1) & 3] + dy * Level.DY[(dir + 1) & 3];
        if (Math.abs(r) >= Math.abs(f)) return r < 0 ? "TO YOUR LEFT" : "TO YOUR RIGHT";
        return f > 0 ? "AHEAD OF YOU" : "BEHIND YOU";
    }

    private void updateDoors(float dt) {
        for (int y = 0; y < lv.h; y++)
            for (int x = 0; x < lv.w; x++) {
                if (lv.doorAnim[y][x] > 0) {
                    lv.doorAnim[y][x] += dt / 0.55f;
                    if (lv.doorAnim[y][x] >= 1) {
                        lv.doorAnim[y][x] = 0;
                        lv.cell[y][x] = Level.OPEN;
                        markSeen();
                    }
                }
            }
    }

    private void updateParty(float dt) {
        for (Member m : party) {
            if (m.cd > 0) m.cd = Math.max(0, m.cd - dt);
            if (m.hurtFlash > 0) m.hurtFlash -= dt;
            if (m.swing > 0) m.swing -= dt;
        }
    }

    // ---------------------------------------------------------------- monsters
    private int[][] dist;

    private void computeDist() {
        if (dist == null) dist = new int[lv.h][lv.w];
        for (int[] r : dist) java.util.Arrays.fill(r, 999);
        int[] qx = new int[lv.w * lv.h], qy = new int[lv.w * lv.h];
        int head = 0, tail = 0;
        dist[py][px] = 0; qx[tail] = px; qy[tail++] = py;
        if (anim == A_FWD || anim == A_BACK || anim == A_STRAFE) { dist[toY][toX] = 0; qx[tail] = toX; qy[tail++] = toY; }
        while (head < tail) {
            int x = qx[head], y = qy[head++];
            for (int d = 0; d < 4; d++) {
                int nx = x + Level.DX[d], ny = y + Level.DY[d];
                if (!lv.passable(nx, ny) || dist[ny][nx] <= dist[y][x] + 1) continue;
                dist[ny][nx] = dist[y][x] + 1;
                qx[tail] = nx; qy[tail++] = ny;
            }
        }
    }

    private boolean partyOn(int x, int y) {
        if (x == px && y == py) return true;
        return (anim == A_FWD || anim == A_BACK || anim == A_STRAFE) && x == toX && y == toY;
    }

    private void updateMonsters(float dt) {
        computeDist();
        for (Monster m : lv.monsters) {
            if (!m.alive()) continue;
            m.idleT += dt;
            if (m.attackAnim > 0) m.attackAnim -= dt;
            if (m.hitFlash > 0) m.hitFlash -= dt;
            if (m.moveT < 1) m.moveT = Math.min(1, m.moveT + dt / 0.4f);
            int d = dist[m.y][m.x];
            if (!m.awake && d <= 6) {
                m.awake = true;
                if (d <= 3) say("A " + m.label + " STIRS " + relWhere(m.x, m.y) + "!", Pal.RED_L);
            }
            if (!m.awake) continue;
            boolean adjacent = Math.abs(m.x - px) + Math.abs(m.y - py) == 1 && m.moveT >= 1 && anim != A_FWD && anim != A_BACK && anim != A_STRAFE;
            if (adjacent) {
                m.attackCd -= dt;
                if (m.attackCd <= 0) {
                    m.attackCd = m.attackEvery * (0.85f + rnd.nextFloat() * 0.3f);
                    m.attackAnim = 0.4f;
                    monsterHits(m);
                }
            } else {
                m.moveCd -= dt;
                if (m.moveCd <= 0 && m.moveT >= 1 && d < 999) {
                    m.moveCd = m.moveEvery;
                    int best = -1, bd = d;
                    for (int k = 0; k < 4; k++) {
                        int nx = m.x + Level.DX[k], ny = m.y + Level.DY[k];
                        if (!lv.passable(nx, ny) || partyOn(nx, ny) || lv.monsterAt(nx, ny) != null) continue;
                        if (dist[ny][nx] < bd) { bd = dist[ny][nx]; best = k; }
                    }
                    if (best >= 0) {
                        m.fromX = m.x; m.fromY = m.y;
                        m.x += Level.DX[best]; m.y += Level.DY[best];
                        m.moveT = 0;
                        m.attackCd = Math.max(m.attackCd, m.attackEvery * 0.5f);
                    }
                }
            }
        }
    }

    private void monsterHits(Monster m) {
        int dx = m.x - px, dy = m.y - py;
        int from = 0;
        for (int d = 0; d < 4; d++) if (Level.DX[d] == dx && Level.DY[d] == dy) from = d;
        int[] pool;
        if (from == dir) pool = new int[]{0, 1};
        else if (from == ((dir + 2) & 3)) pool = new int[]{2, 3};
        else pool = new int[]{0, 1, 2, 3};
        ArrayList<Member> cand = new ArrayList<>();
        for (int i : pool) if (party[i].alive()) cand.add(party[i]);
        if (cand.isEmpty()) for (Member p : party) if (p.alive()) cand.add(p);
        if (cand.isEmpty()) return;
        Member t = cand.get(rnd.nextInt(cand.size()));
        if (rnd.nextFloat() < 0.12f) {
            say("THE " + m.label + " MISSES " + t.name + ".", Pal.STONE6);
            return;
        }
        int dmg = m.dmgMin + rnd.nextInt(m.dmgMax - m.dmgMin + 1);
        t.hp = Math.max(0, t.hp - dmg);
        t.hurtFlash = 0.35f;
        shake = Math.max(shake, 0.18f);
        String verb = m.type.equals("ghoul") ? "CLAWS" : m.type.equals("wraith") ? "CHILLS" : "CUTS";
        String where = from == dir ? "" : from == ((dir + 2) & 3) ? " FROM BEHIND" : relWhere(m.x, m.y).replace("TO YOUR", "FROM THE");
        say("THE " + m.label + " " + verb + " " + t.name + where + " (" + dmg + ")", Pal.RED_L);
        if (!t.alive()) say(t.name + " FALLS!", Pal.RED);
        boolean any = false;
        for (Member p : party) any |= p.alive();
        if (!any) { state = DEAD; stateT = 0; }
    }

    // =================================================================== input
    /** Tap in virtual screen coordinates. */
    public void tap(int x, int y) {
        if (state == TITLE) { if (stateT > 0.4f) { state = PLAY; stateT = 0; } return; }
        if (state == DEAD) { if (stateT > 1.2f) respawn(); return; }
        if (state == WIN) { if (stateT > 1.5f) { newGame(); state = TITLE; stateT = 0; } return; }
        // view: use what's in front
        if (x >= VX && x < VX + 128 && y >= VY && y < VY + 128) { input(showMap ? ACT_MAP : ACT_USE); return; }
        // left column
        if (x < VX - 2) {
            if (y >= VY && y < VY + 24) { input(ACT_MAP); return; }
            if (y >= VY + 28 && y < VY + 56) { input(ACT_POTION); return; }
        }
        if (x >= VX + 130) {
            if (y >= VY + 52 && y < VY + 76) { input(ACT_USE); return; }
        }
        // party weapons
        for (int i = 0; i < 4; i++) {
            int bx = panelX(i), by = panelY(i);
            if (x >= bx && x < bx + PANEL_W && y >= by && y < by + PANEL_H) { input(ACT_ATTACK0 + i); return; }
        }
        // movement pad
        int a = padHit(x, y);
        if (a >= 0) input(a);
    }

    private int panelX(int i) { return (i & 1) == 0 ? 3 : 3 + PANEL_W + 2; }
    private int panelY(int i) { return partyY + (i >> 1) * (PANEL_H + 2); }

    private int padX0() { return (W - (3 * BTN + 2 * BTN_GAP)) / 2; }

    /** Movement-pad action under a point, or -1 (used for hold-to-repeat). */
    public int padAction(int x, int y) { return state == PLAY ? padHit(x, y) : -1; }

    public boolean idle() { return anim == A_NONE && queue.isEmpty(); }

    private int padHit(int x, int y) {
        int x0 = padX0();
        int[][] grid = {{ACT_TURNL, ACT_FWD, ACT_TURNR}, {ACT_LEFT, ACT_BACK, ACT_RIGHT}};
        for (int r = 0; r < 2; r++)
            for (int c = 0; c < 3; c++) {
                int bx = x0 + c * (BTN + BTN_GAP), by = padY + r * (BTN + BTN_GAP);
                if (x >= bx - 2 && x < bx + BTN + 2 && y >= by - 2 && y < by + BTN + 2) return grid[r][c];
            }
        return -1;
    }

    /** Desktop keys and taps funnel here; movement queues one action while animating. */
    public void input(int a) {
        if (state != PLAY) { tap(0, 0); return; }
        boolean move = a <= ACT_TURNR;
        if (move && anim != A_NONE) {
            if (queue.size() < 1) queue.add(a);
            return;
        }
        act(a);
    }

    private void act(int a) {
        switch (a) {
            case ACT_FWD: step(dir, A_FWD); break;
            case ACT_BACK: step((dir + 2) & 3, A_BACK); break;
            case ACT_LEFT: step((dir + 3) & 3, A_STRAFE); animSide = -1; break;
            case ACT_RIGHT: step((dir + 1) & 3, A_STRAFE); animSide = 1; break;
            case ACT_TURNL: turn(-1); break;
            case ACT_TURNR: turn(1); break;
            case ACT_USE: use(); break;
            case ACT_MAP: showMap = !showMap; break;
            case ACT_POTION: drink(); break;
            default:
                if (a >= ACT_ATTACK0 && a < ACT_ATTACK0 + 4) attack(a - ACT_ATTACK0);
        }
    }

    private void turn(int s) {
        fromDir = dir;
        dir = (dir + s + 4) & 3;
        anim = A_TURN; animT = 0; animSide = s;
    }

    private void step(int d, int kind) {
        int nx = px + Level.DX[d], ny = py + Level.DY[d];
        char c = lv.at(nx, ny);
        if (c == Level.STAIRS && kind == A_FWD) { descend(); return; }
        if (!lv.passable(nx, ny) || lv.monsterAt(nx, ny) != null) {
            anim = A_BUMP; animT = 0; shake = Math.max(shake, 0.08f);
            if (lv.monsterAt(nx, ny) != null) say("A " + lv.monsterAt(nx, ny).label + " BLOCKS THE WAY.", Pal.STONE7);
            return;
        }
        toX = nx; toY = ny; anim = kind; animT = 0;
    }

    private void descend() {
        state = WIN; stateT = 0;
    }

    private void use() {
        int fx = px + Level.DX[dir], fy = py + Level.DY[dir];
        char c = lv.at(fx, fy);
        int face = (dir + 2) & 3;
        String deco = lv.deco(fx, fy, face);
        if ("switch".equals(deco)) {
            lv.setDeco(fx, fy, face, "switch_on");
            switchPressed = true;
            shake = 0.12f;
            say("CLICK. THE LOOSE BRICK SINKS INTO THE WALL.", Pal.BONE);
            if (secretX >= 0) secretT = 0;
            return;
        }
        if ("switch_on".equals(deco)) { say("THE BRICK WILL NOT MOVE AGAIN.", Pal.STONE7); return; }
        switch (c) {
            case Level.DOOR:
                if (lv.doorAnim[fy][fx] <= 0) { lv.doorAnim[fy][fx] = 0.001f; say("THE DOOR GROANS UPWARD.", Pal.STONE8); }
                return;
            case Level.LOCKED:
                if (keys > 0) {
                    keys--;
                    lv.cell[fy][fx] = Level.DOOR;
                    lv.doorAnim[fy][fx] = 0.001f;
                    say("THE IRON KEY TURNS. THE LOCK GIVES.", Pal.GOLD);
                } else say("LOCKED. YOU NEED A KEY.", Pal.STONE7);
                return;
            case Level.BARS: say("THE CELL DOOR IS LOCKED FROM OUTSIDE.", Pal.STONE7); return;
            case Level.SECRET: say("A STONE SLAB BED, BUILT INTO THE WALL.", Pal.STONE7); return;
            case Level.SHRINE: shrine(); return;
            case Level.STAIRS: descend(); return;
            default: break;
        }
        Monster m = lv.monsterAt(fx, fy);
        if (m != null) { say("TAP A WARRIOR'S WEAPON TO STRIKE.", Pal.STONE7); return; }
        if (deco != null && deco.equals("chains")) { say("RUSTED SHACKLES. STILL WARM.", Pal.STONE7); return; }
        if (deco != null && deco.equals("sigil")) { say("THE CURSE SIGIL PULSES LIKE A HEART.", Pal.CURSE_L); return; }
        if (deco != null && deco.equals("sconce")) { say("THE TORCH BURNS WITHOUT HEAT.", Pal.FLAME); return; }
        if (lv.solid(fx, fy)) say("COLD, SWEATING STONE.", Pal.STONE6);
    }

    private void shrine() {
        for (Member m : party) { if (!m.alive()) say(m.name + " RISES AGAIN.", Pal.TEAL_L); m.hp = m.maxHp; }
        cpX = px; cpY = py; cpDir = dir;
        say("THE GRAVE SHRINE MENDS YOUR FLESH.", Pal.TEAL_L);
        floaters.add(new Floater("MENDED", Pal.TEAL_L, 64, 70));
    }

    private void drink() {
        if (potions <= 0) { say("YOU HAVE NO GRAVE BLOOD.", Pal.STONE7); return; }
        Member best = null;
        for (Member m : party) if (m.alive() && m.hp < m.maxHp && (best == null || m.hp * best.maxHp < best.hp * m.maxHp)) best = m;
        if (best == null) { say("NO ONE NEEDS TO DRINK.", Pal.STONE7); return; }
        potions--;
        int heal = Math.min(best.maxHp - best.hp, 22);
        best.hp += heal;
        say(best.name + " DRINKS GRAVE BLOOD (+" + heal + ")", Pal.RED_L);
    }

    private void attack(int i) {
        Member a = party[i];
        if (!a.alive() || a.cd > 0) return;
        Monster target = null;
        int range = a.reach == Member.RANGED ? 4 : 1;
        boolean frontRow = i < 2 || (!party[0].alive() && !party[1].alive());
        if (a.reach == Member.MELEE && !frontRow) range = 0;
        int x = px, y = py;
        for (int k = 1; k <= range; k++) {
            x += Level.DX[dir]; y += Level.DY[dir];
            Monster m = lv.monsterAt(x, y);
            if (m != null && m.moveT > 0.5f) { target = m; break; }
            if (!lv.passable(x, y)) break;
        }
        a.swing = 0.25f;
        if (target == null) {
            a.cd = 0.5f;
            floaters.add(new Floater(range == 0 ? "CAN'T REACH" : "NO TARGET", Pal.STONE6, 64, 60));
            return;
        }
        a.cd = a.cooldown;
        target.awake = true;
        if (rnd.nextFloat() < 0.1f + target.evade) {
            floaters.add(new Floater("MISS", Pal.STONE7, 64 + rnd.nextInt(16) - 8, 50));
            return;
        }
        int dmg = a.dmgMin + rnd.nextInt(a.dmgMax - a.dmgMin + 1) + (plevel - 1);
        target.hp -= dmg;
        target.hitFlash = 0.14f;
        floaters.add(new Floater("" + dmg, Pal.FLAME, 64 + rnd.nextInt(20) - 10, 46));
        if (!target.alive()) {
            say(a.name + " DESTROYS THE " + target.label + ".", Pal.GOLD);
            xp += target.xp;
            int need = plevel * plevel * 20;
            if (xp >= need) {
                plevel++;
                for (Member m : party) { m.maxHp += 6; if (m.alive()) m.hp = Math.min(m.maxHp, m.hp + 12); }
                say("THE CURSE FEEDS YOU. LEVEL " + plevel + "!", Pal.CURSE_L);
            }
        }
    }

    private void respawn() {
        px = cpX; py = cpY; dir = cpDir;
        for (Member m : party) m.hp = Math.max(1, m.maxHp / 2);
        anim = A_NONE; queue.clear();
        for (Monster m : lv.monsters) { m.awake = false; m.moveT = 1; m.fromX = m.x; m.fromY = m.y; }
        state = PLAY; stateT = 0;
        say("THE CURSE WILL NOT LET YOU REST.", Pal.CURSE_L);
    }

    private void markSeen() {
        int fx = Level.DX[dir], fy = Level.DY[dir], rx = Level.DX[(dir + 1) & 3], ry = Level.DY[(dir + 1) & 3];
        for (int dz = 0; dz <= 3; dz++)
            for (int dx = -1; dx <= 1; dx++) {
                int x = px + fx * dz + rx * dx, y = py + fy * dz + ry * dx;
                if (x < 0 || y < 0 || x >= lv.w || y >= lv.h) continue;
                lv.seen[y][x] = true;
                if (lv.solid(x, y) && dx == 0) return;
            }
    }

    // =================================================================== render
    public void render() {
        drawBackground();
        if (state == TITLE) { drawTitle(); return; }
        drawView();
        drawSideColumns();
        drawLog();
        drawParty();
        drawPad();
        if (state == DEAD) drawDead();
        if (state == WIN) drawWin();
    }

    private void drawBackground() {
        g.clear(Pal.STONE0);
        for (int y = 0; y < H; y += 8) {
            g.fill(0, y, W, 1, Pal.INK);
            int off = ((y >> 3) & 1) * 10;
            for (int x = -20 + off; x < W; x += 20) g.fill(x, y + 1, 1, 7, Pal.INK);
            for (int x = -20 + off; x < W; x += 20) g.fill(x + 1, y + 1, 19, 1, Pal.STONE1);
        }
    }

    private void drawView() {
        // frame: iron and brass
        g.fill(VX - 5, VY - 5, 138, 138, Pal.INK);
        g.fill(VX - 4, VY - 4, 136, 136, Pal.BRASS);
        g.fill(VX - 3, VY - 3, 134, 134, Pal.WOOD_D);
        g.fill(VX - 2, VY - 2, 132, 132, Pal.GOLD);
        g.fill(VX - 1, VY - 1, 130, 130, Pal.INK);
        for (int[] c : new int[][]{{VX - 5, VY - 5}, {VX + 128, VY - 5}, {VX - 5, VY + 128}, {VX + 128, VY + 128}}) {
            g.fill(c[0], c[1], 5, 5, Pal.STEEL);
            g.fill(c[0] + 1, c[1] + 1, 3, 3, Pal.STEEL_L);
            g.fill(c[0] + 2, c[1] + 2, 1, 1, Pal.INK);
        }
        int sxo = 0, syo = 0;
        if (shake > 0) { sxo = rnd.nextInt(3) - 1; syo = rnd.nextInt(3) - 1; }
        if (showMap && state == PLAY) { drawMap(); return; }
        int[] buf = renderViewNow();
        g.copy(buf, 128, 0, 0, VX + sxo, VY + syo, 128, 128);
        if (sxo != 0 || syo != 0) {
            // keep the frame clean when shaking
            g.fill(VX - 1, VY - 1, 130, 1, Pal.INK); g.fill(VX - 1, VY + 128, 130, 1, Pal.INK);
            g.fill(VX - 1, VY - 1, 1, 130, Pal.INK); g.fill(VX + 128, VY - 1, 1, 130, Pal.INK);
        }
        for (Floater f : floaters) g.textC(f.s, VX + (int) f.x, VY + (int) f.y, f.c);
        if (bannerT > 0 && state == PLAY) {
            String n = lv.name.toUpperCase();
            int bw = Gfx.width(n) + 12;
            g.shade(VX + 64 - bw / 2, VY + 6, bw, 13, 110);
            g.textC(n, VX + 64, VY + 9, Pal.CURSE_L);
        }
    }

    private int[] pan = new int[256 * 128];

    private int[] renderViewNow() {
        float t = Math.min(animT, 0.999f);
        switch (anim) {
            case A_FWD: {
                int sz = Math.min(3, 1 + (int) (t * 3));
                vr.render(lv, px, py, dir, 0, sz, time);
                return vr.out.px;
            }
            case A_BACK: {
                int sz = 3 - Math.min(2, (int) (t * 3));
                vr.render(lv, toX, toY, dir, 0, sz, time);
                return vr.out.px;
            }
            case A_STRAFE: {
                if (t < 0.5f) vr.render(lv, px, py, dir, 2 * animSide, 0, time);
                else vr.render(lv, toX, toY, dir, -2 * animSide, 0, time);
                return vr.out.px;
            }
            case A_BUMP: {
                vr.render(lv, px, py, dir, 0, t < 0.5f ? 1 : 0, time);
                return vr.out.px;
            }
            case A_TURN: {
                // the old view slides out while the new one slides in, like the 90s crawlers did
                vr.render(lv, px, py, fromDir, 0, 0, time);
                vr2.render(lv, px, py, dir, 0, 0, time);
                int step = Math.min(3, 1 + (int) (t * 3));
                int off = step * 32;
                int[] a = vr.out.px, b = vr2.out.px, o = vr.out.px.clone();
                for (int y = 0; y < 128; y++) {
                    for (int x = 0; x < 128; x++) {
                        int v;
                        if (animSide > 0) { int sx = x + off; v = sx < 128 ? a[y * 128 + sx] : b[y * 128 + sx - 128]; }
                        else { int sx = x - off; v = sx >= 0 ? a[y * 128 + sx] : b[y * 128 + sx + 128]; }
                        o[y * 128 + x] = v;
                    }
                }
                return o;
            }
            default:
                vr.render(lv, px, py, dir, 0, 0, time);
                return vr.out.px;
        }
    }

    private void drawMap() {
        g.fill(VX, VY, 128, 128, 0xff1a1611);
        int cs = 7;
        int ox = VX + 64 - (px * cs + cs / 2), oy = VY + 64 - (py * cs + cs / 2);
        for (int y = 0; y < lv.h; y++)
            for (int x = 0; x < lv.w; x++) {
                if (!lv.seen[y][x]) continue;
                int sx = ox + x * cs, sy = oy + y * cs;
                if (sx < VX || sy < VY || sx + cs > VX + 128 || sy + cs > VY + 128) continue;
                char c = lv.at(x, y);
                int col;
                switch (c) {
                    case Level.FLOOR: col = 0xff8f8368; break;
                    case Level.OPEN: col = 0xffa26833; break;
                    case Level.DOOR: col = Pal.WOOD; break;
                    case Level.LOCKED: col = Pal.BRASS; break;
                    case Level.BARS: col = Pal.STEEL; break;
                    case Level.STAIRS: col = Pal.TEAL; break;
                    case Level.SHRINE: col = Pal.TEAL_L; break;
                    default: col = 0xff352f24;
                }
                g.fill(sx, sy, cs, cs, col);
                if (!lv.solid(x, y)) g.frame(sx, sy, cs, cs, 0xff786c54);
            }
        // party arrow
        int cx = ox + px * cs + cs / 2, cy = oy + py * cs + cs / 2;
        for (int k = -2; k <= 2; k++) {
            int ax = cx + Level.DX[dir] * 2 + Level.DY[dir] * 0, ay = cy + Level.DY[dir] * 2;
            g.fill(cx + Level.DX[dir] * k - (Level.DY[dir] != 0 ? 0 : 0), cy + Level.DY[dir] * k, 1, 1, Pal.RED);
        }
        g.fill(cx - 1, cy - 1, 3, 3, Pal.RED);
        g.fill(cx + Level.DX[dir] * 3, cy + Level.DY[dir] * 3, 1, 1, Pal.RED_L);
        g.textS("MAP", VX + 4, VY + 4, Pal.PARCH);
    }

    private void drawSideColumns() {
        // left: map and potions
        g.panel(2, VY, 20, 24, Pal.STONE2, Pal.STONE4, Pal.STONE1);
        g.blit(atlas.get("ui:map"), 6, VY + 6);
        g.panel(2, VY + 28, 20, 28, Pal.STONE2, Pal.STONE4, Pal.STONE1);
        g.blit(atlas.get("ui:potion"), 6, VY + 31);
        g.textC("" + potions, 12, VY + 45, potions > 0 ? Pal.RED_L : Pal.STONE5);
        g.panel(2, VY + 60, 20, 28, Pal.STONE2, Pal.STONE4, Pal.STONE1);
        g.blit(atlas.get("ui:key"), 6, VY + 63);
        g.textC("" + keys, 12, VY + 77, keys > 0 ? Pal.GOLD : Pal.STONE5);
        // right: compass and use
        int rx = VX + 132;
        g.panel(rx, VY, 20, 24, Pal.WOOD_D, Pal.WOOD, Pal.INK);
        g.textC("" + Level.DIRS.charAt(dir), rx + 10, VY + 4, Pal.GOLD);
        g.fill(rx + 6, VY + 14, 8, 1, Pal.BRASS);
        g.fill(rx + 9, VY + 13, 2, 3, Pal.RED);
        g.panel(rx, VY + 28, 20, 20, Pal.STONE2, Pal.STONE4, Pal.STONE1);
        g.textC("L" + plevel, rx + 10, VY + 34, Pal.CURSE_L);
        g.panel(rx, VY + 52, 20, 24, Pal.STONE2, Pal.STONE4, Pal.STONE1);
        g.blit(atlas.get("ui:use"), rx + 4, VY + 58);
    }

    private void drawLog() {
        g.panel(3, logY, W - 6, 46, 0xff0c0706, Pal.WOOD_D, Pal.WOOD_D);
        g.frame(4, logY + 1, W - 8, 44, Pal.WOOD);
        int y = logY + 4;
        for (int i = 0; i < log.size(); i++) {
            Msg m = log.get(i);
            int c = i == log.size() - 1 ? m.c : dim(m.c);
            g.text(m.s, 8, y, c);
            y += 8;
        }
    }

    private static int dim(int c) {
        int r = ((c >> 16) & 255) * 3 / 5, gg = ((c >> 8) & 255) * 3 / 5, b = (c & 255) * 3 / 5;
        return 0xff000000 | (r << 16) | (gg << 8) | b;
    }

    private void drawParty() {
        for (int i = 0; i < 4; i++) {
            Member m = party[i];
            int x = panelX(i), y = panelY(i);
            boolean hurt = m.hurtFlash > 0;
            g.panel(x, y, PANEL_W, PANEL_H, hurt ? Pal.BLOOD : Pal.STONE2, hurt ? Pal.RED : Pal.STONE4, Pal.STONE1);
            // portrait
            g.fill(x + 3, y + 3, 42, 42, Pal.INK);
            g.blit(atlas.get("p:" + m.portrait), x + 4, y + 4, m.alive() ? 0 : 2, 0, 0, W, H);
            if (!m.alive()) {
                g.shade(x + 4, y + 4, 40, 40, 140);
                g.textC("DEAD", x + 24, y + 20, Pal.RED);
            }
            // name & row
            g.textS(m.name, x + 48, y + 4, m.alive() ? Pal.BONE : Pal.STONE5);
            // weapon button
            int wx = x + 52, wy = y + 14;
            boolean ready = m.alive() && m.cd <= 0;
            g.panel(wx, wy, 26, 26, ready ? Pal.WOOD : Pal.STONE1, ready ? Pal.GOLD : Pal.STONE3, Pal.INK);
            int bob = m.swing > 0 ? -2 : 0;
            g.blit(atlas.get("ui:wpn_" + m.weapon), wx + 3, wy + 3 + bob, ready ? 0 : 2, 0, 0, W, H);
            if (m.alive() && m.cd > 0) {
                int hh = (int) (22 * m.cd / m.cooldown);
                g.shade(wx + 2, wy + 24 - hh, 22, hh, 120);
            }
            // hp bar
            int bw = PANEL_W - 8;
            g.fill(x + 3, y + 47, bw + 2, 5, Pal.INK);
            int hpw = m.maxHp > 0 ? bw * m.hp / m.maxHp : 0;
            int col = m.hp * 3 < m.maxHp ? Pal.RED : m.hp * 3 < m.maxHp * 2 ? Pal.FIRE : Pal.GREEN;
            g.fill(x + 4, y + 48, hpw, 3, col);
            g.fill(x + 4, y + 48, hpw, 1, 0xffacbf6b & (col | 0xff000000));
            String hpS = m.hp + "/" + m.maxHp;
            g.text(hpS, x + PANEL_W - 4 - Gfx.width(hpS), y + 41 - 1, Pal.STONE7);
        }
    }

    private void drawPad() {
        int x0 = padX0();
        String[][] icons = {{"turnl", "fwd", "turnr"}, {"left", "back", "right"}};
        for (int r = 0; r < 2; r++)
            for (int c = 0; c < 3; c++) {
                int bx = x0 + c * (BTN + BTN_GAP), by = padY + r * (BTN + BTN_GAP);
                g.panel(bx, by, BTN, BTN, Pal.STONE3, Pal.STONE6, Pal.STONE1);
                g.fill(bx + 3, by + 3, BTN - 6, BTN - 6, Pal.STONE2);
                g.blit(atlas.get("ui:arr_" + icons[r][c]), bx + 8, by + 8);
            }
        // decorative skull-lamps either side of the pad
        g.blit(atlas.get("ui:skull"), 8, padY + 26);
        g.blit(atlas.get("ui:skull"), W - 20, padY + 26);
    }

    private void drawTitle() {
        // the cell view behind the title
        vr.render(lv, lv.startX, lv.startY, lv.startDir, 0, 0, time);
        int vy = H / 2 - 64 - 10;
        g.fill(VX - 2, vy - 2, 132, 132, Pal.INK);
        g.copy(vr.out.px, 128, 0, 0, VX, vy, 128, 128);
        g.shade(VX, vy, 128, 128, 150);
        String t = "GRAVEBORNE";
        int tw = Gfx.width(t) * 2;
        int ty = vy - 54;
        g.text(t, W / 2 - tw / 2 + 2, ty + 2, Pal.CURSE_D, 2);
        g.text(t, W / 2 - tw / 2 + 1, ty + 1, Pal.CURSE, 2);
        g.text(t, W / 2 - tw / 2, ty, Pal.BONE, 2);
        g.textC("THE RISEN DEAD", W / 2, ty + 22, Pal.TEAL_L);
        g.textC("AGAINST THE ETERNAL CURSE", W / 2, ty + 32, Pal.TEAL_L);
        if (((int) (time * 2) & 1) == 0) g.textC("TAP TO RISE", W / 2, vy + 140, Pal.GOLD);
        g.textC("FLOOR I: THE OUBLIETTE", W / 2, H - 20, Pal.STONE6);
    }

    private void drawDead() {
        g.shade(0, 0, W, H, 90);
        g.textC("THE CURSE", W / 2, H / 2 - 20, Pal.RED, 2);
        g.textC("RECLAIMS YOU", W / 2, H / 2, Pal.RED);
        if (stateT > 1.2f) g.textC("TAP TO RISE AGAIN", W / 2, H / 2 + 20, Pal.STONE8);
    }

    private void drawWin() {
        g.shade(0, 0, W, H, 70);
        g.textC("YOU DESCEND", W / 2, H / 2 - 30, Pal.TEAL_L);
        g.textC("DEEPER INTO THE CURSE...", W / 2, H / 2 - 18, Pal.TEAL_L);
        g.textC("END OF FLOOR I", W / 2, H / 2 + 4, Pal.GOLD);
        if (stateT > 1.5f) g.textC("TAP TO RETURN", W / 2, H / 2 + 24, Pal.STONE8);
    }
}
