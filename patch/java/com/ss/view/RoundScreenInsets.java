package com.ss.view;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.text.TextUtils;
import android.util.DisplayMetrics;
import android.view.View;
import android.view.ViewGroup;
import android.view.animation.Animation;
import android.widget.GridView;
import android.widget.ListAdapter;
import android.widget.TextView;

/**
 * DouqiuOS tuning for Square Home's app-drawer list view.
 *
 * 全部行为都由 設定 → 程式抽屜 →「DouqiuOS 適配」里的选项控制（写进应用默认 SharedPreferences）：
 *   douqiuFitMode      0=關閉(默认) 1=貼弧 2=直欄
 *   douqiuFitStrength  貼弧/直欄 的收邊強度 %（默认 100，范围 50~200，由 MyIntPreference 提供）
 *   douqiuFade         邊緣漸隱 開/關（默认开）
 *   douqiuFadeScale    漸隱長度 = 底部導覽列高度 × 這個百分比（默认 100% = 与底栏一致）
 *   douqiuAnimSpeed    抽屜項目動畫時長倍率 %（默认 100）
 *   douqiuVideoWallpaper 視頻壁紙：應用內 MediaPlayer(MediaCodec 硬解)+SurfaceView 循環播放本地視頻
 *   douqiuVideoPath      視頻路徑（留空則自動找 /sdcard/SquareHome2/wallpaper.mp4 等）
 *
 * 几何说明见 README：圆心用窗口坐标（display 中心 − rootView 屏幕位置），
 * 行用 offsetLeftAndRight() 平移（不触发重排、命中框同步），行宽不变。
 */
public final class RoundScreenInsets {

    private static final String LIST_ADAPTER = "com.ss.squarehome2.g0";
    private static final int ID_FRAME_ICON = 0x7f090141;   // @id/frameIcon
    private static final int ID_TEXT_LABEL = 0x7f0902ec;   // @id/textLabel
    private static final int DIMEN_MENU_BAR_HEIGHT = 0x7f07028c;  // @dimen/menu_bar_height (44dp)

    private static final int EDGE_MARGIN = 2;

    private static final String PREF_MODE = "douqiuFitMode";
    private static final String PREF_STRENGTH = "douqiuFitStrength";
    private static final String PREF_FADE = "douqiuFade";
    private static final String PREF_FADE_SCALE = "douqiuFadeScale";
    private static final String PREF_ANIM = "douqiuAnimSpeed";
    private static final String PREF_VIDEO = "douqiuVideoWallpaper";
    private static final String PREF_VIDEO_PATH = "douqiuVideoPath";

    /** 缓存的动画倍率 / 动态壁纸开关（给没有 Context 的钩子用） */
    private static volatile int sAnimPercent = 100;
    private static volatile boolean sSkipWallpaper = false;

    private RoundScreenInsets() {
    }

    // ------------------------------------------------------------------ 供 smali 钩子调用
    /** 抽屜項目動畫時長倍率（AnimateGridView 里 startAnimation 前调用） */
    public static void scaleAnimation(Animation a) {
        try {
            if (a == null) {
                return;
            }
            final int p = sAnimPercent;
            if (p == 100 || p <= 0) {
                return;
            }
            long d = a.getDuration();
            if (d <= 0) {
                d = 200;
            }
            long nd = d * p / 100;
            a.setDuration(nd < 30 ? 30 : nd);
        } catch (Throwable t) {
        }
    }

    /** 视频壁纸模式下跳过应用自绘壁纸（fk.k(Canvas) 开头调用） */
    public static boolean skipWallpaper() {
        return sSkipWallpaper;
    }

    // ------------------------------------------------------------------ 主流程
    public static void applyToGridView(GridView gv) {
        if (gv == null) {
            return;
        }
        try {
            final int count = gv.getChildCount();
            if (count <= 0) {
                return;
            }
            if (gv.getNumColumns() != 1) {                 // 列表模式专用
                return;
            }
            ListAdapter adapter = gv.getAdapter();
            if (adapter == null || !LIST_ADAPTER.equals(adapter.getClass().getName())) {
                return;
            }

            final Context ctx = gv.getContext();
            final SharedPreferences sp = prefs(ctx);
            final int mode = readInt(sp, PREF_MODE, 0);            // 0 off / 1 arc / 2 column
            final int strength = clamp(readInt(sp, PREF_STRENGTH, 100), 10, 300);
            final boolean fadeOn = sp.getBoolean(PREF_FADE, true);
            final int fadeScale = clamp(readInt(sp, PREF_FADE_SCALE, 100), 10, 300);
            sAnimPercent = clamp(readInt(sp, PREF_ANIM, 100), 10, 500);
            // 视频壁纸：开着就跳过应用自绘壁纸，并让 DouqiuVideoWallpaper 在最底层放视频
            final boolean videoOn = sp.getBoolean(PREF_VIDEO, false);
            final String videoPath = sp.getString(PREF_VIDEO_PATH, "");
            sSkipWallpaper = videoOn;
            if (ctx instanceof Activity) {
                DouqiuVideoWallpaper.apply((Activity) ctx, videoOn, videoPath);
            }

            final DisplayMetrics dm = gv.getResources().getDisplayMetrics();
            setupFadingEdge(gv, dm, fadeOn, fadeScale);
            if (mode == 0) {                               // 关闭：把行还原到底
                resetRows(gv);
                return;
            }

            final int w = dm.widthPixels;
            final int h = dm.heightPixels;
            final int r = Math.min(w, h) / 2;
            if (r <= 0 || w <= 0 || h <= 0) {
                return;
            }
            final double rr = (double) r * (double) r;
            final int cap = r / 2;

            int[] rootLoc = new int[2];
            gv.getRootView().getLocationOnScreen(rootLoc);
            final int cy = h / 2 - rootLoc[1];
            final int cx = w / 2 - rootLoc[0];

            int[] gvLoc = new int[2];
            gv.getLocationInWindow(gvLoc);
            final int gvTop = gvLoc[1];
            final int gvLeft = gvLoc[0];
            final int cxLocal = cx - gvLeft;

            int columnGap = -1;
            if (mode == 2) {
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
            }

            for (int i = 0; i < count; i++) {
                final View row = gv.getChildAt(i);
                if (row == null) {
                    continue;
                }

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

                int gap;
                if (mode == 2) {
                    gap = columnGap;
                } else {
                    final int bandTop = gvTop + row.getTop() + topInRow;
                    final int bandBottom = bandTop + bandHeight;
                    final int d1 = Math.abs(bandTop - cy);
                    final int d2 = Math.abs(bandBottom - cy);
                    final int ym = d1 > d2 ? d1 : d2;
                    if (ym >= r) {
                        gap = cap;
                    } else {
                        int g = (int) Math.ceil(cxLocal - Math.sqrt(rr - (double) ym * (double) ym));
                        if (g < 0) {
                            g = 0;
                        }
                        gap = g > cap ? cap : g;
                    }
                }
                gap = gap * strength / 100;                 // 曲率强度

                int offset = gap + EDGE_MARGIN - leftInRow;
                if (offset < 0) {
                    offset = 0;
                }

                final int want = gv.getPaddingLeft() + offset;
                final int cur = row.getLeft();
                if (want != cur) {
                    row.offsetLeftAndRight(want - cur);
                }

                final View label = row.findViewById(ID_TEXT_LABEL);
                if (label instanceof TextView) {
                    final TextView tv = (TextView) label;
                    if (tv.getEllipsize() == null) {
                        tv.setEllipsize(TextUtils.TruncateAt.END);
                    }
                }
            }
        } catch (Throwable t) {
            // 任何异常都只是不生效，不能让桌面崩
        }
    }

    // ------------------------------------------------------------------ 内部
    private static void resetRows(GridView gv) {
        final int base = gv.getPaddingLeft();
        for (int i = 0; i < gv.getChildCount(); i++) {
            final View row = gv.getChildAt(i);
            if (row != null && row.getLeft() != base) {
                row.offsetLeftAndRight(base - row.getLeft());
            }
        }
    }

    /** 渐隐边：长度 = 底栏高度 × fadeScale%；关掉时恢复应用默认（关闭） */
    private static void setupFadingEdge(GridView gv, DisplayMetrics dm, boolean on, int scalePercent) {
        if (!on) {
            if (gv.isVerticalFadingEdgeEnabled()) {
                gv.setVerticalFadingEdgeEnabled(false);
            }
            return;
        }
        int bar;
        try {
            bar = gv.getResources().getDimensionPixelSize(DIMEN_MENU_BAR_HEIGHT);
        } catch (Throwable t) {
            bar = 0;
        }
        if (bar <= 0) {
            bar = Math.round(44f * dm.density);
        }
        final int fade = Math.max(1, bar * scalePercent / 100);
        if (!gv.isVerticalFadingEdgeEnabled() || gv.getCacheColorHint() != 0) {
            gv.setCacheColorHint(0);
            gv.setFadingEdgeLength(fade);
            gv.setVerticalFadingEdgeEnabled(true);
        }
    }

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(ctx.getPackageName() + "_preferences", Context.MODE_PRIVATE);
    }

    /** MyIntPreference 存 int；MyListPreference 存 String —— 两种都兼容 */
    private static int readInt(SharedPreferences sp, String key, int def) {
        try {
            final Object v = sp.getAll().get(key);
            if (v instanceof Integer) {
                return ((Integer) v).intValue();
            }
            if (v instanceof String) {
                return Integer.parseInt(((String) v).trim());
            }
            if (v instanceof Long) {
                return ((Long) v).intValue();
            }
        } catch (Throwable t) {
        }
        return def;
    }

    private static int clamp(int v, int lo, int hi) {
        return v < lo ? lo : (v > hi ? hi : v);
    }
}
