import streamlit as st
import subprocess
import os
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import whisper
from PIL import Image, ImageDraw, ImageFont

st.title("批量视频每秒截图 + 旁白叠加工具")
st.write("支持 ≥5 个视频同时处理，每秒截图 + 时间水印 + 底部旁白文字")

uploaded_files = st.file_uploader("选择视频文件（MP4/AVI/MOV）", 
                                  type=["mp4", "avi", "mov"], 
                                  accept_multiple_files=True)

if uploaded_files:
    st.write(f"已上传 {len(uploaded_files)} 个视频")
    
    if st.button("开始批量处理"):
        with tempfile.TemporaryDirectory() as tmpdirname:
            output_base = os.path.join(tmpdirname, "outputs")
            os.makedirs(output_base, exist_ok=True)
            zip_path = os.path.join(tmpdirname, "screenshots.zip")
            
            def process_video(file):
                video_path = os.path.join(tmpdirname, file.name)
                with open(video_path, "wb") as f:
                    f.write(file.getbuffer())
                
                folder = os.path.join(output_base, file.name.split('.')[0])
                os.makedirs(folder, exist_ok=True)
                
                # 1. 每秒截图 + 时间水印
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', 'fps=1,drawtext=text=\'%{pts\\:hms}\':x=w-tw-10:y=h-th-10:fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5',
                    '-vsync', '0',
                    os.path.join(folder, 'frame_%03d.png')
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                
                # 2. 提取音频
                audio_path = os.path.join(tmpdirname, f"{file.name}.wav")
                subprocess.run(['ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', audio_path], check=True, capture_output=True)
                
                # 3. Whisper 转录
                model = whisper.load_model("base")
                result = model.transcribe(audio_path)
                segments = result['segments']
                
                # 4. 给每张图加底部旁白
                for fname in sorted(os.listdir(folder)):
                    if fname.endswith('.png'):
                        frame_num = int(fname.split('_')[1].split('.')[0])
                        t = frame_num - 1
                        text = ''
                        for seg in segments:
                            if seg['start'] <= t < seg['end']:
                                text += seg['text'].strip() + ' '
                        if text:
                            img_path = os.path.join(folder, fname)
                            im = Image.open(img_path)
                            draw = ImageDraw.Draw(im)
                            font = ImageFont.load_default(size=20)
                            bbox = draw.textbbox((0,0), text, font=font)
                            text_w = bbox[2] - bbox[0]
                            text_h = bbox[3] - bbox[1]
                            x = (im.width - text_w) // 2
                            y = im.height - text_h - 15
                            draw.rectangle((x-10, y-8, x+text_w+10, y+text_h+8), fill=(0,0,0,180))
                            draw.text((x, y), text.strip(), font=font, fill="white")
                            im.save(img_path)
                
                os.remove(audio_path)
                return f"✅ 处理完成：{file.name}"
            
            # 并行处理（同时跑5个）
            with ThreadPoolExecutor(max_workers=5) as exe:
                futures = [exe.submit(process_video, f) for f in uploaded_files]
                for future in as_completed(futures):
                    st.write(future.result())
            
            # 打包 ZIP
            with zipfile.ZipFile(zip_path, 'w') as z:
                for root, _, files in os.walk(output_base):
                    for f in files:
                        z.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), output_base))
            
            st.success("全部处理完成！")
            with open(zip_path, "rb") as f:
                st.download_button("📥 下载 ZIP 包", f, file_name="screenshots.zip", mime="application/zip")
