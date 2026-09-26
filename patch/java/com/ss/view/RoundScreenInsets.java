package com.ss.view;

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
 * DouqiuOS 圆屏适配：应用抽屉列表视图的收边 + 上下边缘渐隐 + 抽屉动画流速。
 *
 * 设置（設定 → 程式抽屜 →「DouqiuOS 適配」，全部用应用自己用过的 MySwitchPreference / MyIntPreference）：
 *   douqiuRoundFit        圓屏適配      默认关；关 = 原版观感
 *   douqiuRoundFitColumn  直欄模式      开 = 所有行同一栏
 *   douqiuSoftCurve       柔性曲線      开 = 弧只跟到一定程度就停（行不会大幅参差）
 *   douqiuFitStrength     貼弧強度 %    50~200（100 = 按圆弧精确计算）
 *   douqiuFade            邊緣漸隱      默认开
 *   douqiuFadeScale       漸隱大小 %    相对底部导航栏高度（100 = 与底栏同高）
 *   douqiuAnimSpeed       動畫流速 %    50~200（抽屉项目动画 / 弹性回弹动画时长倍率）
 *
 * 模式：关 / 貼弧（逐行跟随圆弧）/ 柔性曲線（跟随但有上限）/ 直欄（全部同一栏）。
 */
public final class RoundScreenInsets {

    private static final String LIST_ADAPTER = "com.ss.squarehome2.g0";
    private static final int ID_FRAME_ICON = 0x7f090141;          // @id/frameIcon
    private static final int ID_TEXT_LABEL = 0x7f0902ec;          // @id/textLabel
    private static final int DIMEN_MENU_BAR_HEIGHT = 0x7f07028c;  // @dimen/menu_bar_height (44dp)

    private static final int EDGE_MARGIN = 2;
    /** 柔性曲線的上限（≈33dp）：超过这个收边量就不再跟，行不会大幅参差 */
    private static final float SOFT_CURVE_DP = 33f;

    private static final String PREF_FIT = "douqiuRoundFit";
    private static final String PREF_COLUMN = "douqiuRoundFitColumn";
    private static final String PREF_SOFT = "douqiuSoftCurve";
    private static final String PREF_STRENGTH = "douqiuFitStrength";
    private static final String PREF_FADE = "douqiuFade";
    private static final String PREF_FADE_SCALE = "douqiuFadeScale";
    private static final String PREF_ANIM = "douqiuAnimSpeed";

    /** 缓存的动画倍率（给没有 Context 的钩子用） */
    private static volatile int sAnimPercent = 100;

    private RoundScreenInsets() {
    }

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
            final long nd = d * p / 100;
            a.setDuration(nd < 30 ? 30 : nd);
        } catch (Throwable t) {
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
            if (gv.getNumColumns() != 1) {                        // 列表模式专用
                return;
            }
            ListAdapter adapter = gv.getAdapter();
            if (adapter == null || !LIST_ADAPTER.equals(adapter.getClass().getName())) {
                return;
            }

            final SharedPreferences sp = prefs(gv.getContext());
            final int strength = clamp(readInt(sp, PREF_STRENGTH, 100), 10, 300);
            sAnimPercent = clamp(readInt(sp, PREF_ANIM, 100), 10, 500);

            setupFadingEdge(gv, sp.getBoolean(PREF_FADE, true),
                    clamp(readInt(sp, PREF_FADE_SCALE, 100), 10, 300));

            if (!sp.getBoolean(PREF_FIT, false)) {                 // 关闭：把行还原到底
                resetRows(gv);
                return;
            }
            final boolean column = sp.getBoolean(PREF_COLUMN, false);
            final boolean soft = sp.getBoolean(PREF_SOFT, false);

            final DisplayMetrics dm = gv.getResources().getDisplayMetrics();
            final int w = dm.widthPixels;
            final int h = dm.heightPixels;
            final int r = Math.min(w, h) / 2;
            if (r <= 0 || w <= 0 || h <= 0) {
                return;
            }
            final double rr = (double) r * (double) r;
            final int cap = r / 2;                                 // 不把行推到屏幕中间
            final int softCap = Math.max(1, Math.round(SOFT_CURVE_DP * dm.density));

            int[] rootLoc = new int[2];
            gv.getRootView().getLocationOnScreen(rootLoc);
            final int cy = h / 2 - rootLoc[1];
            final int cx = w / 2 - rootLoc[0];

            int[] gvLoc = new int[2];
            gv.getLocationInWindow(gvLoc);
            final int gvTop = gvLoc[1];
            final int cxLocal = cx - gvLoc[0];

            int columnGap = -1;
            if (column) {                                          // 直栏：整段可见区取最紧弦
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
                if (column) {
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
                gap = gap * strength / 100;                       // 貼弧強度
                if (soft && gap > softCap) {                      // 柔性曲線
                    gap = softCap;
                }

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

    private static void resetRows(GridView gv) {
        final int base = gv.getPaddingLeft();
        for (int i = 0; i < gv.getChildCount(); i++) {
            final View row = gv.getChildAt(i);
            if (row != null && row.getLeft() != base) {
                row.offsetLeftAndRight(base - row.getLeft());
            }
        }
    }

    /** 原生 fading edge：长度 = 底部导航栏高度 × fadeScale%；关掉时恢复应用默认（关闭） */
    private static void setupFadingEdge(GridView gv, boolean on, int scalePercent) {
        if (!on) {
            if (gv.isVerticalFadingEdgeEnabled()) {
                gv.setVerticalFadingEdgeEnabled(false);
            }
            return;
        }
        if (!gv.isVerticalFadingEdgeEnabled() || gv.getCacheColorHint() != 0) {
            int bar;
            try {
                bar = gv.getResources().getDimensionPixelSize(DIMEN_MENU_BAR_HEIGHT);
            } catch (Throwable t) {
                bar = 0;
            }
            if (bar <= 0) {
                bar = Math.round(44f * gv.getResources().getDisplayMetrics().density);
            }
            gv.setCacheColorHint(0);      // 不设这个，渐隐区会画成实心色块
            gv.setFadingEdgeLength(Math.max(1, bar * scalePercent / 100));
            gv.setVerticalFadingEdgeEnabled(true);
        }
    }

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(ctx.getPackageName() + "_preferences", Context.MODE_PRIVATE);
    }

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
