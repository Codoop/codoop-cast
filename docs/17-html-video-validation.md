# 首个 HTML 动画视频样例

> 状态说明：本文保留对应开发阶段的计划或验证记录。当前已实现能力与发布缺口以 [Alpha 发布状态](29-release-readiness.md) 为准；首次使用见 [安装指南](28-install-and-first-video.md)。

2026-10-17，阶段：维护者原型验证。目标是将已经验收的 72 秒配音和字幕，经过标准分镜、实际时间轴和 HTML 动画，合成为完整 MP4。尚未新增 storyboard/scenes/video skills 或通用 video setup 注册；不要向用户宣称这些能力已可通过安装插件直接使用。

## 分镜与交接

本话题制作 10 个表达单元：话题到视频、确定问题、聚焦表达、整理资料、通俗解释、口播结构、生成配音、检查声音、音画同步、成片收尾。具体画面与动画在样例 HTML 中创作，不是后续话题必须遵循的十类模板。

标准制作包包含 script、video-script、assets、scene、audio、alignment、timeline、output-profile 八类 JSON，以及相对路径引用的 HTML、旁白和 SRT。script/audio/alignment 来自本次正式字幕任务 bb1c99acd09849278d872171ba605042，其原始配音 SHA-256 与已验收版本一致。review.json 记录本次会话中用户对同一音频及字幕同步的确认；只接受这个样例，不扩展为新输入自动通过。

video-script 的动画锚点增加 text_range，以段落 ID + Unicode 码点 [start,end) 指定具体词语，避免重复词语指向不明。timeline 编译器用真实对齐单元解析样本位置，不依字数推算秒数。零时长字组合造成的组级精度仍保留，无法声称组内每个字有独立精度。

分镜内容结束与播放结束分开：开头覆盖初始静音，后一个镜头开始之前保留当前镜头，结尾覆盖完整声音尾部。动画事件必须落在镜头时间范围内。改稿后保留未变分镜内容，重新解析受影响锚点和后续偏移；复用机制目前是结构设计，不宣称已经实现一键局部修改工作流。

## HTML 场景契约原型

样例入口 examples/72-second-workflow/scenes/index.html，实现 window.CodoopCast：

- configure(bundle)：接收 profile、timeline、alignment 和本话题的 visuals 数据。
- ready：字体等场景资源就绪。
- renderAt(seconds)：直接重建对应时刻画面，不依赖之前如何播放。
- inspect()：返回可检查的布局与运行时问题。

动画值由真实时间计算，不使用自由运行的 CSS 动画或随机数驱动画面。交互预览以原声 currentTime 驱动；导出模式不加载音频播放器、不监听播放器的 timeupdate，音轨由 FFmpeg 合成，避免播放器事件将导出帧重置。

HTML 有竖屏上下组织与横屏左右组织两种布局，不将竖屏简单拉伸。字幕按配置字体尺寸和位置显示，使用平衡换行，保留条目末尾无标点规则。右下为抽象人物占位，未实现真人头像视频或口型同步。

## 本地渲染

私有 envs/video：Python 3.10.11、Playwright 1.56.0、imageio-ffmpeg 0.6.0、jsonschema 4.23.0；Chromium Headless Shell 141.0.7390.37 / build 1194，缓存位于私有 browsers/video。冻结依赖在 constraints-video-experiment-windows.txt。本次手动准备，不假装 generic setup 已支持 video。

scripts/make_video_demo.py 是此演示话题的编辑脚本，不是通用的自动分镜算法。scripts/render_video.py 接受制作包，先验证依赖、真实时间范围与已就绪场景，再用 file URI 打开本地 HTML，按帧时刻定位并导出截图。浏览器上下文禁用外网请求；不启动 HTTP 服务。这不等同于系统级防火墙离线证明。

帧通过内存管道交给 FFmpeg，不生成成千上万张临时图片。输出 H.264/AAC、30fps、faststart，使用 BT.709 limited-range yuv420p 转换，避免将浏览器 JPEG 的 full-range 标记直接带入交付文件。当前旁白保留 32k 单声道；目标平台的音频规格预设尚待实现。

两种画幅均为 72 秒、2160 帧：1080×1920 与 1920×1080。每个分镜抽取代表帧，检查正文/字幕不越界及不与头像重叠。全片解码、音视频时长、颜色和流参数在最终导出后核查。

最终交付：codoop-cast-portrait-final.mp4（3,572,504 字节）、codoop-cast-landscape-v3.mp4（3,315,849 字节）。两者全片解码通过，H.264/AAC、30fps、72 秒、limited-range yuv420p；两份可编辑制作包合并为 codoop-cast-video-projects.zip。抽查编码后画面，修正横屏标题将“画面”拆行的问题，并在样例 inspect 中加入标题意外换行检查。

重复定位检查同时比较可见 DOM 与画面。Chromium 图层重建可能引入低幅抗锯齿差异：允许每通道最大差值不超过 3、全图平均绝对差不超过 0.1，并要求可见 DOM 完全一致；不以像素差异检测代替时间轴验证，也不声称所有浏览器或机器字节级复现。报告记录原始差异指标。

## 验证与边界

43 项测试通过（37 项普通测试、6 项制作包契约测试）。新增检查覆盖版本不一致、未确认对齐、非法时间、词语锚点、事件越出分镜，以及初始/镜头间静音覆盖。两种制作包通过八类 schema 与跨文件检查。

本样例无需生图或外部素材，全部图形为本地 HTML/CSS/SVG。中文使用本机 Microsoft YaHei，不分发系统字体；跨机器字体复现与可分发字体选择尚未解决。样例包含的音频是生成的旁白，不包含个人参考录音或声音模型。

仍需用户观看判断表达、节奏和风格。未实现：通用自动分镜、任意话题场景生成 skill、通用 video setup、场景缓存/局部重渲染、复杂素材轨道、真实头像输入及平台投稿预设。下一步应先依据样片反馈调整场景协议，再独立封装 storyboard、scenes、video 三个 skill。

一手参考：[Playwright 浏览器管理](https://playwright.dev/python/docs/browsers)、[截图接口](https://playwright.dev/python/docs/api/class-page#page-screenshot)、[FFmpeg scale 颜色与范围选项](https://ffmpeg.org/ffmpeg-filters.html#scale)。


2026-10-17 更新：storyboard/scenes/video 三个独立 skill、共享 authoring/video setup 及公开本地命令已实现并验证，最新状态与限制以[视频 Skills 运行说明](18-video-skills-running.md)为准。
