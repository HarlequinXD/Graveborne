import com.harlequin.graveborne.*;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.File;
import java.nio.file.Files;

/** Desktop test harness: plays a scripted session and saves screenshots.
 *  java Harness <assetsDir> <outDir> <script...>
 *  script tokens: f b l r tl tr use map pot a0..a3 wait:<sec> shot:<name> tap:x,y mid:<name> */
public class Harness {
    public static void main(String[] a) throws Exception {
        final File dir = new File(a[0]);
        Atlas.Loader ld = new Atlas.Loader() {
            public int[] image(String n, int[] sz) {
                try {
                    BufferedImage im = ImageIO.read(new File(dir, n));
                    sz[0] = im.getWidth(); sz[1] = im.getHeight();
                    return im.getRGB(0, 0, sz[0], sz[1], null, 0, sz[0]);
                } catch (Exception e) { throw new RuntimeException(e); }
            }
            public String text(String n) {
                try { return new String(Files.readAllBytes(new File(dir, n).toPath()), "UTF-8"); }
                catch (Exception e) { throw new RuntimeException(e); }
            }
        };
        long t0 = System.nanoTime();
        Game g = new Game(ld, 390);
        System.out.println("load ms " + (System.nanoTime() - t0) / 1000000);
        File out = new File(a[1]); out.mkdirs();
        for (int i = 2; i < a.length; i++) {
            String s = a[i];
            if (s.startsWith("wait:")) run(g, Float.parseFloat(s.substring(5)));
            else if (s.startsWith("shot:")) { g.render(); save(g, new File(out, s.substring(5) + ".png")); }
            else if (s.startsWith("mid:")) { run(g, 0.09f); g.render(); save(g, new File(out, s.substring(4) + ".png")); }
            else if (s.startsWith("go:")) { String[] p = s.substring(3).split(","); g.debugGo(p[0], Integer.parseInt(p[1]), Integer.parseInt(p[2]), Integer.parseInt(p[3])); }
            else if (s.startsWith("tp:")) { String[] p = s.substring(3).split(","); g.px = Integer.parseInt(p[0]); g.py = Integer.parseInt(p[1]); g.dir = Integer.parseInt(p[2]); }
            else if (s.equals("dbg")) { System.out.println("pos " + g.px + "," + g.py + " dir " + g.dir + " cellAhead " + g.lv.at(g.px + Level.DX[g.dir], g.py + Level.DY[g.dir])); }
            else if (s.startsWith("tap:")) { String[] p = s.substring(4).split(","); g.tap(Integer.parseInt(p[0]), Integer.parseInt(p[1])); run(g, 0.05f); }
            else {
                int act;
                switch (s) {
                    case "f": act = Game.ACT_FWD; break; case "b": act = Game.ACT_BACK; break;
                    case "l": act = Game.ACT_LEFT; break; case "r": act = Game.ACT_RIGHT; break;
                    case "tl": act = Game.ACT_TURNL; break; case "tr": act = Game.ACT_TURNR; break;
                    case "use": act = Game.ACT_USE; break; case "map": act = Game.ACT_MAP; break;
                    case "pot": act = Game.ACT_POTION; break;
                    default: act = Game.ACT_ATTACK0 + Integer.parseInt(s.substring(1));
                }
                g.input(act);
                if (!s.startsWith("a") && !s.equals("use") && !s.equals("map") && !s.equals("pot")) run(g, 0.0f);
            }
        }
        // timing
        t0 = System.nanoTime();
        for (int i = 0; i < 200; i++) { g.update(1 / 60f); g.render(); }
        System.out.println("frame us " + (System.nanoTime() - t0) / 200000);
    }

    static void run(Game g, float sec) {
        int n = Math.max(1, Math.round(sec * 60));
        for (int i = 0; i < n; i++) g.update(1 / 60f);
    }

    static void save(Game g, File f) throws Exception {
        int k = 3;
        BufferedImage im = new BufferedImage(Game.W * k, g.H * k, BufferedImage.TYPE_INT_RGB);
        for (int y = 0; y < g.H * k; y++) for (int x = 0; x < Game.W * k; x++) im.setRGB(x, y, g.g.px[(y / k) * Game.W + x / k]);
        ImageIO.write(im, "png", f);
    }
}
