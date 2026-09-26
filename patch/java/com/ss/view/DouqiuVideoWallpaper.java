package com.ss.view;

import android.app.Activity;
import android.graphics.drawable.ColorDrawable;
import android.media.MediaPlayer;
import android.net.Uri;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.view.ViewGroup;

import java.io.File;

/**
 * 应用内「视频壁纸」：MediaPlayer(底层就是 MediaCodec 硬解) + SurfaceView 循环播放本地视频，
 * 插在窗口最底层当壁纸用。
 *
 * 为什么不走系统 Live Wallpaper：手表 ROM 没有 live wallpaper 服务。
 * 为什么不用 FFmpeg：Android 上 FFmpeg 的「硬解」本身就是转调 MediaCodec
 * (h264_mediacodec/hevc_mediacodec)，直接让 MediaPlayer 走 MediaCodec 是同一颗硬解单元，
 * 却不用打包 20~40MB 的 .so 与 JNI 胶水；只有当视频是 MediaCodec 不支持的编码时才需要 FFmpeg。
 */
public final class DouqiuVideoWallpaper {

    /** 没填路径时按顺序找这几个位置 */
    private static final String[] DEFAULT_PATHS = {
            "/sdcard/SquareHome2/wallpaper.mp4",
            "/sdcard/SquareHome2/video-wallpaper.mp4",
            "/sdcard/Movies/wallpaper.mp4",
            "/sdcard/Download/wallpaper.mp4",
            "/sdcard/wallpaper.mp4",
    };

    private static SurfaceView sView;
    private static MediaPlayer sPlayer;
    private static String sCurrent;

    private DouqiuVideoWallpaper() {
    }

    public static void apply(Activity a, boolean on, String path) {
        try {
            if (!on) {
                stop();
                return;
            }
            final File f = pick(path);
            if (f == null) {
                return;
            }
            if (sPlayer != null && f.getAbsolutePath().equals(sCurrent) && sPlayer.isPlaying()) {
                return;                                   // 已经在放同一个文件
            }
            stop();

            final ViewGroup root = (ViewGroup) a.getWindow().getDecorView();
            // 让窗口/根视图透明，视频才透得出来（应用内容照常画在上面）
            a.getWindow().setBackgroundDrawable(new ColorDrawable(0));
            root.setBackgroundColor(0);
            final View content = root.getChildAt(0);
            if (content != null) {
                content.setBackgroundColor(0);
            }

            final SurfaceView sv = new SurfaceView(a);
            root.addView(sv, 0, new ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
            sView = sv;
            sv.getHolder().addCallback(new SurfaceHolder.Callback() {
                @Override
                public void surfaceCreated(SurfaceHolder h) {
                    try {
                        final MediaPlayer mp = new MediaPlayer();
                        mp.setDataSource(a, Uri.fromFile(f));
                        mp.setLooping(true);
                        mp.setVolume(0f, 0f);
                        mp.setDisplay(h);
                        mp.prepare();
                        mp.start();
                        sPlayer = mp;
                        sCurrent = f.getAbsolutePath();
                    } catch (Throwable t) {
                        stop();
                    }
                }

                @Override
                public void surfaceChanged(SurfaceHolder h, int format, int w, int hh) {
                }

                @Override
                public void surfaceDestroyed(SurfaceHolder h) {
                    stop();
                }
            });
        } catch (Throwable t) {
            // 任何失败都只是"没有视频壁纸"，不影响桌面
        }
    }

    private static File pick(String path) {
        try {
            if (path != null && path.trim().length() > 0) {
                final File f = new File(path.trim());
                if (f.isFile()) {
                    return f;
                }
            }
            for (String p : DEFAULT_PATHS) {
                final File f = new File(p);
                if (f.isFile()) {
                    return f;
                }
            }
        } catch (Throwable t) {
        }
        return null;
    }

    private static void stop() {
        try {
            if (sPlayer != null) {
                sPlayer.stop();
                sPlayer.release();
            }
        } catch (Throwable t) {
        }
        sPlayer = null;
        sCurrent = null;
        try {
            final View v = sView;
            if (v != null && v.getParent() instanceof ViewGroup) {
                ((ViewGroup) v.getParent()).removeView(v);
            }
        } catch (Throwable t) {
        }
        sView = null;
    }
}
