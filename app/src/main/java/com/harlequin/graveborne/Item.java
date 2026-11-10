package com.harlequin.graveborne;

/** Something lying on the floor: key, potion, or just old bones (scenery). */
public final class Item {
    public final String type;
    public final int x, y;

    public Item(String type, int x, int y) { this.type = type; this.x = x; this.y = y; }

    public boolean pickable() { return !type.equals("bones"); }
}
