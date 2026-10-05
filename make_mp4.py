import moviepy.editor as mpy
from pathlib import Path

def png_to_mp4(png_paths, out_path, frame_delay_sec):
    clips = [
        mpy.ImageClip(img.as_posix()).set_duration(frame_delay_sec)
        for img in png_paths
        ]
    vid = mpy.concatenate_videoclips(clips, method="compose")
    vid.write_videofile(
        out_path.as_posix(),
        fps=int(1/frame_delay_sec),
        codec="libx264",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
        )

if __name__=="__main__":
    fig_dir = Path("/home/mtdodson/store/GHCNh/figures/")
    png_dir = fig_dir.joinpath("monthly")
    out_path = fig_dir.joinpath("ghcnh_nobs_monthly.mp4")
    png_paths = list(sorted(list(png_dir.iterdir())))
    png_to_mp4(
        png_paths=png_paths,
        out_path=out_path,
        frame_delay_sec=0.2,
        )
