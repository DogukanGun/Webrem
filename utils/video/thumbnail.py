from io import BytesIO

import ffmpeg


def extract_thumbnail(video_path: str) -> BytesIO:
    process = (
        ffmpeg
        .input(video_path, ss=1)
        .output('pipe:', vframes=1, format='image2', vcodec='png')
        .run_async(pipe_stdout=True, pipe_stderr=True)
    )
    out, err = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {err.decode()}")
    return BytesIO(out)
