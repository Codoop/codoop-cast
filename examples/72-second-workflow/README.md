# 72 秒口播的制作包示例

这是结构契约示例，不是已经完成的视频。稿件来自本项目已验收的 304 字演示稿；不伪造调研报告或证据。4 个段落为了演示旧任务适配，与已生成音频块对应，正式内容段落和 TTS 块允许多对多映射。

- script.json：原稿、配音稿与稳定段落 ID。
- video-script.json：4 个分镜、屏幕文字及基于段落的动画锚点；本示例不需要图片，不强制生图。
- assets.json：空素材集合，可后续按分镜需求增加。
- scene.json：待制作的 HTML 场景清单，不包含可执行场景。
- audio.json：真实音频的采样率、总采样数和分块边界，以及到稿件的文本范围映射。个人声音文件不分发，路径为空。
- alignment.json：待运行真实对齐，字词时间和字幕为空。
- timeline.json：明确标记 blocked，不填估算镜头时间。
- output-profile.json：可修改的 1080×1920、30fps 示例，包含字幕及头像占位配置，不代表用户已选择默认画幅。
- package.json：产物相对路径及内容 SHA-256。

更改任一文件后须更新 package.json 摘要。草案验证使用隔离工具环境安装 jsonschema==4.23.0，运行 `scripts/validate_production.py examples/72-second-workflow`。有效只代表已实现的契约检查通过，不表示时间对齐、字体布局、媒体编码或视觉效果通过验收。
