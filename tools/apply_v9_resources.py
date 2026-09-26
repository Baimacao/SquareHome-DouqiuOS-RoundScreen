#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v9 的改动：把 RoundScreenInsets 里的动态壁纸开关换成「应用内视频壁纸」，
   并新增对应文案 / 设置行（原生 LWP 手表没有服务，换掉）。"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
W = r"E:\B1807\Documents\DSH\squarehome-mod"
DEC = os.path.join(W, "decoded")

# ---------- 1) RoundScreenInsets.java ----------
p = os.path.join(W, "src", "com", "ss", "view", "RoundScreenInsets.java")
t = io.open(p, encoding="utf-8").read()
t = t.replace('    private static final String PREF_LWP = "douqiuLiveWallpaper";',
              '    private static final String PREF_VIDEO = "douqiuVideoWallpaper";\n'
              '    private static final String PREF_VIDEO_PATH = "douqiuVideoPath";')
t = t.replace("""            sAnimPercent = clamp(readInt(sp, PREF_ANIM, 100), 10, 500);
            sSkipWallpaper = sp.getBoolean(PREF_LWP, false);
            applyWindow(ctx);""",
              """            sAnimPercent = clamp(readInt(sp, PREF_ANIM, 100), 10, 500);
            // 视频壁纸：开着就跳过应用自绘壁纸，并让 DouqiuVideoWallpaper 在最底层放视频
            final boolean videoOn = sp.getBoolean(PREF_VIDEO, false);
            final String videoPath = sp.getString(PREF_VIDEO_PATH, "");
            sSkipWallpaper = videoOn;
            if (ctx instanceof Activity) {
                DouqiuVideoWallpaper.apply((Activity) ctx, videoOn, videoPath);
            }""")
# 去掉不再需要的 applyWindow（原生 LWP 路径）
t = re.sub(r"    /\*\* 动态壁纸：让系统画壁纸（含 LWP）.*?\n    \}\n\n", "", t, flags=re.S)
t = t.replace("import android.graphics.drawable.ColorDrawable;\n", "")
t = t.replace("import android.view.WindowManager;\n", "")
t = t.replace(" *   douqiuLiveWallpaper 動態壁紙：改由系統繪製壁紙（含動態壁紙），本應用程式不再自繪",
              " *   douqiuVideoWallpaper 視頻壁紙：應用內 MediaPlayer(MediaCodec 硬解)+SurfaceView 循環播放本地視頻\n"
              " *   douqiuVideoPath      視頻路徑（留空則自動找 /sdcard/SquareHome2/wallpaper.mp4 等）")
t = t.replace("    /** 动态壁纸模式下跳过应用自绘壁纸（fk.k(Canvas) 开头调用） */",
              "    /** 视频壁纸模式下跳过应用自绘壁纸（fk.k(Canvas) 开头调用） */")
io.open(p, "w", encoding="utf-8", newline="\n").write(t)
print("RoundScreenInsets.java: PREF_VIDEO =", "PREF_VIDEO" in t, "| applyWindow removed =", "applyWindow" not in t)

# ---------- 2) 文案 ----------
NEW_STRINGS = {
    "douqiu_video_title": ("視頻壁紙", "视频壁纸"),
    "douqiu_video_summary": ("應用內用 MediaCodec 硬解循環播放本地視頻當壁紙（不走系統動態壁紙服務，手錶沒有）",
                             "应用内用 MediaCodec 硬解循环播放本地视频当壁纸（不走系统动态壁纸服务，手表没有）"),
    "douqiu_video_path_title": ("視頻檔案路徑", "视频文件路径"),
    "douqiu_video_path_summary": ("例如 /sdcard/SquareHome2/wallpaper.mp4；留空則自動找幾個常見位置",
                                  "例如 /sdcard/SquareHome2/wallpaper.mp4；留空则自动找几个常见位置"),
}
EN_STRINGS = {
    "douqiu_video_title": "Video wallpaper",
    "douqiu_video_summary": "Loop a local video in-app via MediaCodec hardware decoding (no system live-wallpaper service on the watch)",
    "douqiu_video_path_title": "Video file path",
    "douqiu_video_path_summary": "e.g. /sdcard/SquareHome2/wallpaper.mp4; empty = try a few common locations",
}


def add(path, pairs):
    t = io.open(path, encoding="utf-8").read()
    add_list = []
    for k, v in pairs:
        if re.search(r'<string name="%s"' % re.escape(k), t):
            continue
        add_list.append('    <string name="%s">%s</string>' % (k, v))
    if add_list:
        t = t.replace("</resources>", "\n".join(add_list) + "\n</resources>")
        io.open(path, "w", encoding="utf-8", newline="\n").write(t)
    print(f"   {os.path.basename(os.path.dirname(path))}: +{len(add_list)}")


print("2) 新增视频壁纸文案")
add(os.path.join(DEC, "res", "values", "strings.xml"), list(EN_STRINGS.items()))
add(os.path.join(DEC, "res", "values-zh-rTW", "strings.xml"), [(k, v[0]) for k, v in NEW_STRINGS.items()])
add(os.path.join(DEC, "res", "values-zh-rCN", "strings.xml"), [(k, v[1]) for k, v in NEW_STRINGS.items()])

# ---------- 3) prefs_appdrawer.xml：换掉 LWP 行 ----------
p = os.path.join(DEC, "res", "xml", "prefs_appdrawer.xml")
t = io.open(p, encoding="utf-8").read()
old = re.search(r'[ \t]*<com\.ss\.squarehome2\.preference\.MySwitchPreference[^>]*douqiuLiveWallpaper[^>]*/>\n', t)
if old:
    t = t.replace(old.group(0),
                  '        <com.ss.squarehome2.preference.MySwitchPreference android:title="@string/douqiu_video_title" android:summary="@string/douqiu_video_summary" android:key="douqiuVideoWallpaper" android:defaultValue="false" />\n'
                  '        <com.ss.preferencex.EditTextPreference android:title="@string/douqiu_video_path_title" android:summary="@string/douqiu_video_path_summary" android:key="douqiuVideoPath" android:defaultValue="" android:dependency="douqiuVideoWallpaper" />\n')
    io.open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("3) prefs_appdrawer.xml: LWP row -> video wallpaper rows")
else:
    print("3) prefs_appdrawer.xml: LWP row NOT FOUND")
