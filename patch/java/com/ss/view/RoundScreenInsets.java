package com.ss.view;

import android.content.Context;
import android.content.SharedPreferences;
import android.text.TextUtils;
import android.util.DisplayMetrics;
import android.view.View;
import android.view.ViewGroup;
import android.widget.GridView;
import android.widget.ListAdapter;
import android.widget.TextView;

/**
 * DouqiuOS round-screen adaptation for Square Home's app-drawer "list type" view.
 *
 * The watch panel is a 480x480 framebuffer whose visible area is a disc inscribed in it
 * (R = min(w,h)/2). The drawer list is a single-column GridView, so every row is a full-width
 * rectangle whose ends get cut by the round bezel.
 *
 * Two modes, both switchable from 設定 → 程式抽屜 (res/xml/prefs_appdrawer.xml):
 *   douqiuRoundFit        (default on)  master switch; off = original behaviour
 *   douqiuRoundFitColumn  (default off) straight column: every row gets the SAME inset, taken from
 *                                       the chord at the extreme of the visible list band, so the
 *                                       column never moves while scrolling
 *   (both off-default combination)      hugging mode: each row is shifted by the chord of the disc
 *                                       at the icon's own vertical band, so the icon column follows
 *                                       the arc of the bezel
 *
 * Implementation notes
 *  - everything is computed in WINDOW coordinates (child.getTop() space), and the disc centre is
 *    converted from display coordinates into the same space via the root view's screen position.
 *    Mixing screen/display coordinates was the cause of the over-aggressive offsets seen on device;
 *    keeping one coordinate system makes the result independent of where the window sits.
 *  - the row is moved with offsetLeftAndRight(): it does not trigger a layout pass (smooth while
 *    scrolling) and it moves the hit rect with the view, so taps follow what is on screen.
 *  - the row keeps its natural width, so app names are never squeezed away; they may be partly
 *    covered by the bezel, which is what we want.
 *  - the offset is capped at R/2 so no row can be pushed towards the middle of the screen.
 */
public final class RoundScreenInsets {

    /** app-drawer list adapter (R8 name, verified for this APK build) */
    private static final String LIST_ADAPTER = "com.ss.squarehome2.g0";

    /** @id/frameIcon / @id/textLabel in res/layout/item_appdrawer_list.xml (+ _tablet) */
    private static final int ID_FRAME_ICON = 0x7f090141;
    private static final int ID_TEXT_LABEL = 0x7f0902ec;

    /** keep the icon a hair inside the bezel instead of exactly on the mathematical arc */
    private static final int EDGE_MARGIN = 2;

    /** preference keys (see res/xml/prefs_appdrawer.xml) */
    private static final String PREF_FIT = "douqiuRoundFit";
    private static final String PREF_COLUMN = "douqiuRoundFitColumn";

    /** @dimen/menu_bar_height(44dp) —— 抽屉底部导航栏的高度，渐隐长度与它一致 */
    private static final int DIMEN_MENU_BAR_HEIGHT = 0x7f07028c;

    /** 取不到上面那个 dimen 时的兜底长度（dp） */
    private static final float FADING_EDGE_DP = 44f;

    private RoundScreenInsets() {
    }

    /**
     * 打开列表的原生渐隐边（AbsListView 自带能力）。
     * 注意这个 app 自己在 d0.P0() 里把它关掉了（setVerticalFadingEdgeEnabled(false)、长度 5dp），
     * 所以这里按“状态”而不是“标记”判断：被应用再改回去时，下一次滚动会自动补回来。
     * setCacheColorHint(0) 是必须的——否则渐隐区会画成实心色块，而不是透出壁纸。
     * 长度直接取应用自己的 @dimen/menu_bar_height（底部导航栏高度），这样两者永远一致。
     */
    private static void setupFadingEdge(GridView gv, DisplayMetrics dm) {
        // 只用公开 API：getFadingEdgeLength() 是 @hide，所以按“是否已启用 + cacheColorHint”
        // 判断即可——应用在 P0() 里关掉时这两项都会变，下一次滚动就会补回来。
        if (!gv.isVerticalFadingEdgeEnabled() || gv.getCacheColorHint() != 0) {
            int fade;
            try {
                fade = gv.getResources().getDimensionPixelSize(DIMEN_MENU_BAR_HEIGHT);
            } catch (Throwable t) {
                fade = 0;
            }
            if (fade <= 0) {
                fade = Math.round(FADING_EDGE_DP * dm.density);
            }
            gv.setCacheColorHint(0);
            gv.setFadingEdgeLength(fade);
            gv.setVerticalFadingEdgeEnabled(true);
        }
    }

    public static void applyToGridView(GridView gv) {
        if (gv == null) {
            return;
        }
        try {
            final int count = gv.getChildCount();
            if (count <= 0) {
                return;
            }
            if (gv.getNumColumns() != 1) {                 // list type only
                return;
            }
            ListAdapter adapter = gv.getAdapter();
            if (adapter == null || !LIST_ADAPTER.equals(adapter.getClass().getName())) {
                return;
            }

            final Context ctx = gv.getContext();
            // 预设关闭（与 res/xml/prefs_appdrawer.xml 的 defaultValue="false" 一致），
            // 需要时由使用者在 設定 → 程式抽屜 里打开
            final boolean fit = pref(ctx, PREF_FIT, false);
            final boolean column = fit && pref(ctx, PREF_COLUMN, false);

            final DisplayMetrics dm = gv.getResources().getDisplayMetrics();
            setupFadingEdge(gv, dm);                       // 滚出上/下边缘时渐隐（与适配开关无关）
            final int w = dm.widthPixels;
            final int h = dm.heightPixels;
            final int r = Math.min(w, h) / 2;
            if (r <= 0 || w <= 0 || h <= 0) {
                return;
            }
            final double rr = (double) r * (double) r;
            final int cap = r / 2;                          // never push a row to the middle

            // disc centre, display coords -> window coords (same space as child.getTop())
            int[] rootLoc = new int[2];
            gv.getRootView().getLocationOnScreen(rootLoc);
            final int cy = h / 2 - rootLoc[1];
            final int cx = w / 2 - rootLoc[0];

            int[] gvLoc = new int[2];
            gv.getLocationInWindow(gvLoc);
            final int gvTop = gvLoc[1];
            final int gvLeft = gvLoc[0];
            // disc centre in GridView-local coordinates (children report getLeft()/getTop() there)
            final int cxLocal = cx - gvLeft;

            // straight-column mode: one inset for every row, from the visible list band
            final int columnGap;
            if (!fit) {
                columnGap = 0;
            } else if (column) {
                final int bandTop = gvTop + gv.getPaddingTop();
                final int bandBottom = gvTop + gv.getHeight() - gv.getPaddingBottom();
                int ym = Math.abs(bandTop - cy);
                final int d2 = Math.abs(bandBottom - cy);
                if (d2 > ym) {
                    ym = d2;
                }
                int half = 0;
                if (ym < r) {
                    half = (int) Math.sqrt(rr - (double) ym * (double) ym);
                }
                int g = cxLocal - half;
                if (g < 0) {
                    g = 0;
                }
                columnGap = g > cap ? cap : g;
            } else {
                columnGap = -1;                             // unused in hugging mode
            }

            for (int i = 0; i < count; i++) {
                final View row = gv.getChildAt(i);
                if (row == null) {
                    continue;
                }

                // icon geometry inside this row (before first layout: fall back to the whole row)
                int leftInRow = -1;
                int topInRow = 0;
                int bandHeight = 0;
                final View icon = row.findViewById(ID_FRAME_ICON);
                if (icon != null && icon.getHeight() > 0) {
                    View inner = null;
                    if (row instanceof ViewGroup && ((ViewGroup) row).getChildCount() > 0) {
                        inner = ((ViewGroup) row).getChildAt(0);
                    }
                    leftInRow = (inner != null ? inner.getLeft() : 0) + icon.getLeft();
                    topInRow = (inner != null ? inner.getTop() : 0) + icon.getTop();
                    bandHeight = icon.getHeight();
                }
                if (leftInRow < 0 || bandHeight <= 0) {
                    leftInRow = Math.round(10f * dm.density);
                    topInRow = 0;
                    bandHeight = row.getHeight();
                }

                final int gap;
                if (!fit) {
                    gap = 0;
                } else if (column) {
                    gap = columnGap;
                } else {
                    // hugging mode: chord of the disc at the icon's own vertical band
                    final int bandTop = gvTop + row.getTop() + topInRow;
                    final int bandBottom = bandTop + bandHeight;
                    final int d1 = Math.abs(bandTop - cy);
                    final int d2 = Math.abs(bandBottom - cy);
                    final int ym = d1 > d2 ? d1 : d2;
                    int g;
                    if (ym >= r) {
                        g = cap;
                    } else {
                        g = (int) Math.ceil(cxLocal - Math.sqrt(rr - (double) ym * (double) ym));
                        if (g < 0) {
                            g = 0;
                        }
                        if (g > cap) {
                            g = cap;
                        }
                    }
                    gap = g;
                }

                int offset = gap + EDGE_MARGIN - leftInRow;
                if (!fit || offset < 0) {
                    offset = 0;
                }

                final int want = gv.getPaddingLeft() + offset;      // GridView-local coordinates
                final int cur = row.getLeft();
                if (want != cur) {
                    row.offsetLeftAndRight(want - cur);
                }

                // long names used to be cut mid-glyph (lines=1 without ellipsize)
                final View label = row.findViewById(ID_TEXT_LABEL);
                if (label instanceof TextView) {
                    final TextView tv = (TextView) label;
                    if (tv.getEllipsize() == null) {
                        tv.setEllipsize(TextUtils.TruncateAt.END);
                    }
                }
            }
        } catch (Throwable t) {
            // never let the launcher crash because of the inset pass
        }
    }

    /** the app keeps its settings in the default preference file of androidx.preference */
    private static boolean pref(Context ctx, String key, boolean def) {
        try {
            SharedPreferences sp = ctx.getSharedPreferences(
                    ctx.getPackageName() + "_preferences", Context.MODE_PRIVATE);
            return sp.getBoolean(key, def);
        } catch (Throwable t) {
            return def;
        }
    }
}
