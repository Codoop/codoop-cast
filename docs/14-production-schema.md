# 最小制作包结构 v0.1.0

> 状态说明：本文保留对应开发阶段的计划或验证记录。当前已实现能力与发布缺口以 [Alpha 发布状态](29-release-readiness.md) 为准；首次使用见 [安装指南](28-install-and-first-video.md)。

状态：草案与可验证示例，不是已发布运行时协议。JSON Schema 位于 schemas/，示例位于 examples/72-second-workflow/。当前 CLI 不自动读写这些格式，声音适配、对齐和场景实现时继续验证迭代。

实现更新：subtitles CLI 已输出 script/audio/alignment 产物片段；alignment 新增可选 span_basis（spoken_text 或 display_text），未声明时保持旧 spoken_text 语义。正式字幕产物显式使用 display_text，音频范围仍引用实际 spoken_text。完整制作包导入及视频流程尚未实现。

每个产物统一包含 schema_version、kind、artifact_id、revision、data。schema_version 为协议版本，revision 为该产物修改版本；对象 ID 在未替换语义对象时保持稳定。

script、video-script、assets、scene、audio、alignment、timeline、output-profile 各有单独 schema。最小示例包每种一个，由 package.json 索引相对路径与 SHA-256。单个 skill 只需消费其声明依赖，不要求独立使用时集齐八种产物；当前整包验证器要求八种，是此贯穿示例的验收规则，不是所有 skill 输入限制。

script 维护正文；分镜引用段落。音频分块通过 script_spans 引用实际 spoken_text 的 Unicode 码点范围，采用 [start,end) 半开区间，不用 UTF-8 字节或 JavaScript UTF-16 下标。JS 适配需显式按码点转换。分镜和动画引用段落边界，后续加入词语范围锚点时必须升级 schema 并覆盖重复词语场景。

audio 的样本偏移来自真实导出清单。alignment 使用同一音频采样时基；单位和字幕保存起止样本。显示时间、帧号和 SRT 毫秒由这些边界推导，不通过字数均分。脚本不同于分块的映射必须验证，不能仅按相同 ID 猜测。

scene 规定 render-at-time-v1 目标：同一场景版本、布局配置和时间应得到同一画面。当前只定义目标契约，正式 HTML 入口函数、素材加载、字体就绪、动画随机种子等在渲染验证中细化，不宣称任意网页均可导出视频。

alignment pending 与 timeline blocked 可以是有效的规划产物，但不得作为最终渲染就绪。验证器检查 schema、摘要、版本引用及类型、ID、文本映射、时间范围与顺序、动画目标、资源路径和头像边界。它不替代内容覆盖验收、完整 HTML 依赖扫描、真实媒体时长检查或人工预览。

未完成项：独立输入适配器、完整的字词/数字显示映射、音频内容指纹与模型信息标准封装、SRT 取整验证、复杂过渡轨道、字体和平台安全区、横竖屏重排实现、正式运行时集成。当前时间轴仅表达不重叠场景；不把此简化扩展为所有未来轨道都不得重叠。

下一步以此示例验证本地对齐器，再补真实 alignment 和最小 HTML 场景。配音及导出配置变化后，以依赖引用和摘要判定失效；最终只更新相关产物 revision 与引用。
