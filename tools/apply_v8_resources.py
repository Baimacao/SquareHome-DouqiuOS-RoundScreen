#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v8 资源改动：
   1) 补全 app 自己用到、zh-rTW/zh-rCN 缺失的 66 条文案（跳过品牌名/URL/引用）
   2) 新增 DouqiuOS 适配的 4 个可调项文案 + 模式数组
   3) 重写 prefs_appdrawer.xml（关闭/贴弧/直栏 + 强度 + 渐隐 + 动画流速 + 动态壁纸）
   4) AndroidManifest.xml 版本名改为 3.0.1-douqiuos"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DEC = r"E:\B1807\Documents\DSH\squarehome-mod\decoded"

# ---------------------------------------------------------------- 1) 未汉化文案
# name: (zh-rTW, zh-rCN)   —— 跳过 app_name / app_name_en / official_site / l_ip_wait
I18N = {
    "accessibility_permission_required": (
        "此應用程式需要「%s」功能的權限。請在無障礙服務中啟用本應用程式以授權，你可隨時在設定中取消。",
        "此应用程序需要“%s”功能的权限。请在无障碍服务中启用本应用程序以授权，你可随时在设置中取消。"),
    "add_shortcut_error": ("部分捷徑僅在預設桌面上才能正常運作。", "部分快捷方式仅在默认桌面上才能正常工作。"),
    "already_purchased": ("此項目已購買。", "此项目已购买。"),
    "app_wallpaper": ("應用程式桌布", "应用程序壁纸"),
    "buy_product": ("購買商品以解鎖進階功能。", "购买商品以解锁高级功能。"),
    "cancel_yearly_first": ("若要購買此項目，請先在 Google Play 商店取消「Yearly」訂閱。",
                            "若要购买此项目，请先在 Google Play 商店取消“Yearly”订阅。"),
    "cannot_copy_tile": ("選取的磚塊無法複製。", "所选的磁贴无法复制。"),
    "change_daily_wallpaper": ("更換桌布", "更换壁纸"),
    "configure_widget": ("設定小工具", "配置小部件"),
    "contacts_folder": ("聯絡人資料夾", "联系人文件夹"),
    "cube_options": ("立方體選項", "立方体选项"),
    "custom_style": ("非樣式色彩", "非样式颜色"),
    "daily_wallpaper": ("每日桌布", "每日壁纸"),
    "daily_wallpaper_not_set": ("必須啟用每日桌布選項。", "必须启用每日壁纸选项。"),
    "error_no_image_picker": ("沒有可用的圖片挑選程式。", "没有可用的图片选择程序。"),
    "folder_in_folder": ("資料夾中的資料夾", "文件夹中的文件夹"),
    "go_to_home": ("回到桌面", "回到桌面"),
    "hide": ("隱藏", "隐藏"),
    "home_options_en": ("桌面選項", "桌面选项"),
    "key_installed": ("你已安裝金鑰，不需要再進行應用程式內購買。", "你已安装密钥，不需要再进行应用内购买。"),
    "launch_options": ("啟動選項", "启动选项"),
    "lifetime_user": ("你已經是終身使用者！", "你已经是终身用户！"),
    "live_tile": ("動態磚", "动态磁贴"),
    "millisecond": ("毫秒", "毫秒"),
    "monospace": ("等寬字型", "等宽字体"),
    "new_notification": ("新通知", "新通知"),
    "no_daily_wallpaper_folder": ("尚未設定每日桌布的資料夾。", "尚未设置每日壁纸的文件夹。"),
    "no_photo": ("沒有相片", "没有照片"),
    "no_wallpaper": ("沒有桌布", "没有壁纸"),
    "not_selected": ("未選取", "未选择"),
    "not_supported_item": ("目前的 Google Play 商店應用程式版本不支援此項目。",
                           "当前的 Google Play 商店应用程序版本不支持此项目。"),
    "not_supported_wallpaper": ("目前設定的磚塊背景效果不支援所選的桌布類型。",
                                "当前设置的磁贴背景效果不支持所选的壁纸类型。"),
    "per_year": ('" / 年"', '" / 年"'),
    "permission_for_this_widget": ("此小工具需要以下權限才能運作。", "此小部件需要以下权限才能工作。"),
    "pick_wallpaper_image": ("挑選一張圖片作為桌布。", "选择一张图片作为壁纸。"),
    "popup_widget": ("彈出式小工具", "弹出式小部件"),
    "purchase": ("購買", "购买"),
    "purchased": ("已購買", "已购买"),
    "recently_installed": ("最近安裝", "最近安装"),
    "remove": ("移除", "移除"),
    "requires_dynamic_color_scheme": ("此功能需要啟用「動態配色」。要啟用嗎？", "此功能需要启用“动态配色”。要启用吗？"),
    "requires_wallpaper": ("此功能需要先設定桌布。要現在設定嗎？", "此功能需要先设置壁纸。要现在设置吗？"),
    "sans": ("無襯線字型", "无衬线字体"),
    "select_old_backup_folder": ("請在儲存空間中選擇名為「SquareHome2_backups」的資料夾。",
                                 "请在存储空间中选择名为“SquareHome2_backups”的文件夹。"),
    "serif": ("襯線字型", "衬线字体"),
    "set_app_wallpaper": ("設定應用程式桌布", "设置应用程序壁纸"),
    "set_wallpaper_to": ("將桌布設為", "将壁纸设为"),
    "show": ("顯示", "显示"),
    "success_en": ("成功！", "成功！"),
    "system_wallpaper": ("系統桌布", "系统壁纸"),
    "tap_here_to_migrate_old_backups": ("點此移轉舊備份。", "点此迁移旧备份。"),
    "tap_to_grant_permissions": ("點一下以授予權限。", "点一下以授予权限。"),
    "tap_to_set_photo_dir": ("點一下設定相片資料夾。", "点一下设置照片文件夹。"),
    "text": ("文字", "文字"),
    "today_24h": ("'今天' HH:mm", "'今天' HH:mm"),
    "today_24h_m": ("'今天' HH:mm", "'今天' HH:mm"),
    "trial_ended": ("試用期已結束。", "试用期已结束。"),
    "trial_feature_message": ("這是進階功能。", "这是高级功能。"),
    "trial_summary": ("你目前正在免費試用進階功能。", "你目前正在免费试用高级功能。"),
    "troubleshooting": ("疑難排解", "疑难解答"),
    "wallpaper": ("桌布", "壁纸"),
    "wallpaper_folder": ("桌布資料夾", "壁纸文件夹"),
    "wallpaper_folder_summary": ("選擇一個包含每日桌布圖片的資料夾。", "选择一个包含每日壁纸图片的文件夹。"),
    "work_apps": ("公司應用程式", "工作应用程序"),
    "wrong_folder_selected": ("選錯資料夾了。", "选错文件夹了。"),
    "yearly_text1": ("%s 每年計費", "%s 每年计费"),
}

# ---------------------------------------------------------------- 2) 自己的文案
MINE = {
    "douqiu_pref_cat": ("DouqiuOS 適配", "DouqiuOS 适配"),
    "douqiu_fit_mode_title": ("圓屏適配", "圆屏适配"),
    "douqiu_fit_mode_summary": ("應用程式清單的圓屏收邊方式", "应用程序列表的圆屏收边方式"),
    "douqiu_fit_mode_off": ("關閉（原版）", "关闭（原版）"),
    "douqiu_fit_mode_arc": ("貼弧（緊貼圓邊）", "贴弧（紧贴圆边）"),
    "douqiu_fit_mode_column": ("直欄（同一欄對齊）", "直栏（同一栏对齐）"),
    "douqiu_strength_title": ("貼弧強度", "贴弧强度"),
    "douqiu_strength_summary": ("收邊幅度，100% = 依圓弧精確計算", "收边幅度，100% = 按圆弧精确计算"),
    "douqiu_fade_title": ("邊緣漸隱", "边缘渐隐"),
    "douqiu_fade_summary": ("項目滾出上／下邊緣時淡出", "项目滚出上/下边缘时淡出"),
    "douqiu_fade_scale_title": ("漸隱大小", "渐隐大小"),
    "douqiu_fade_scale_summary": ("相對底部導覽列高度，100% = 與導覽列同高",
                                  "相对底部导航栏高度，100% = 与导航栏同高"),
    "douqiu_anim_title": ("動畫流速", "动画流速"),
    "douqiu_anim_summary": ("抽屜項目動畫時長倍率，100% = 原速", "抽屉项目动画时长倍率，100% = 原速"),
    "douqiu_lwp_title": ("動態桌布支援", "动态壁纸支持"),
    "douqiu_lwp_summary": ("改由系統繪製桌布（含動態桌布）；關閉則由本應用程式自行繪製",
                           "改由系统绘制壁纸（含动态壁纸）；关闭则由本应用程序自行绘制"),
}

EN_MINE = {
    "douqiu_pref_cat": "DouqiuOS tuning",
    "douqiu_fit_mode_title": "Round-screen fit",
    "douqiu_fit_mode_summary": "How the app-drawer list follows the round bezel",
    "douqiu_fit_mode_off": "Off (stock)",
    "douqiu_fit_mode_arc": "Hug the arc",
    "douqiu_fit_mode_column": "Straight column",
    "douqiu_strength_title": "Arc strength",
    "douqiu_strength_summary": "Inset amount; 100% = exact chord of the disc",
    "douqiu_fade_title": "Edge fading",
    "douqiu_fade_summary": "Fade rows out as they scroll past the top/bottom edge",
    "douqiu_fade_scale_title": "Fade size",
    "douqiu_fade_scale_summary": "Relative to the bottom nav-bar height; 100% = same as the bar",
    "douqiu_anim_title": "Animation speed",
    "douqiu_anim_summary": "Drawer item animation duration; 100% = stock speed",
    "douqiu_lwp_title": "Live wallpaper",
    "douqiu_lwp_summary": "Let the system draw the wallpaper (incl. live); off = drawn by the app",
}


def insert_strings(path, pairs, label):
    t = io.open(path, encoding="utf-8").read()
    add = []
    for name, value in pairs:
        if re.search(r'<string name="%s"' % re.escape(name), t):
            continue
        add.append('    <string name="%s">%s</string>' % (name, value))
    if not add:
        print(f"  {label}: nothing to add")
        return
    t = t.replace("</resources>", "\n".join(add) + "\n</resources>")
    io.open(path, "w", encoding="utf-8", newline="\n").write(t)
    print(f"  {label}: +{len(add)} strings")


v = os.path.join(DEC, "res", "values")
tw = os.path.join(DEC, "res", "values-zh-rTW")
cn = os.path.join(DEC, "res", "values-zh-rCN")

print("1) 未汉化文案")
insert_strings(os.path.join(tw, "strings.xml"), [(k, x[0]) for k, x in I18N.items()], "zh-rTW")
insert_strings(os.path.join(cn, "strings.xml"), [(k, x[1]) for k, x in I18N.items()], "zh-rCN")

print("2) DouqiuOS 适配文案")
insert_strings(os.path.join(v, "strings.xml"), [(k, x) for k, x in EN_MINE.items()], "default(EN)")
insert_strings(os.path.join(tw, "strings.xml"), [(k, x[0]) for k, x in MINE.items()], "zh-rTW")
insert_strings(os.path.join(cn, "strings.xml"), [(k, x[1]) for k, x in MINE.items()], "zh-rCN")

print("3) 模式数组")
arr = os.path.join(v, "arrays.xml")
t = io.open(arr, encoding="utf-8").read()
if "douqiu_fit_mode_entries" not in t:
    add = """    <string-array name="douqiu_fit_mode_entries">
        <item>@string/douqiu_fit_mode_off</item>
        <item>@string/douqiu_fit_mode_arc</item>
        <item>@string/douqiu_fit_mode_column</item>
    </string-array>
    <string-array name="douqiu_fit_mode_entry_values">
        <item>0</item>
        <item>1</item>
        <item>2</item>
    </string-array>
"""
    t = t.replace("</resources>", add + "</resources>")
    io.open(arr, "w", encoding="utf-8", newline="\n").write(t)
    print("  arrays.xml: +2 arrays")
else:
    print("  arrays.xml: already present")

print("4) AndroidManifest 版本名")
mf = os.path.join(DEC, "AndroidManifest.xml")
t = io.open(mf, encoding="utf-8").read()
t2 = re.sub(r'android:versionName="[^"]*"', 'android:versionName="3.0.1-douqiuos"', t, count=1)
io.open(mf, "w", encoding="utf-8", newline="\n").write(t2)
print("  versionName ->", re.search(r'android:versionName="[^"]*"', t2).group(0), "| changed:", t2 != t)
