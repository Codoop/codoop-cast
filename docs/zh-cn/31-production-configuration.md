# 按配置制作视频

[English](../en/31-production-configuration.md) | [简体中文](31-production-configuration.md)

制作开始先读取共享或项目配置，再确定画面布局。用户只需描述默认要求或本次例外，由 Agent 保存并贯穿工作流。配置仍位于共享 `config.json` 或项目/批次的 `.codoop-cast/config.json`，与 output_language 放在一起。

```json
{
  "schema_version": 1,
  "output_language": "zh-CN",
  "video": {
    "orientation": "portrait",
    "resolution": { "width": 1080, "height": 1920 },
    "fps": 30,
    "subtitle_style": {
      "font_family": "Microsoft YaHei",
      "font_size": 48,
      "color": "#FFFFFF",
      "bottom_margin_ratio": 0.12
    },
    "avatar": {
      "enabled": true,
      "mode": "placeholder",
      "x": 0.78, "y": 0.68,
      "width": 0.14, "height": 0.105
    }
  }
}
```

根目录 `codoop-cast.config.example.json` 提供完整示例。这些默认字体和头像占位面向当前 Windows 路径，不表示所有宿主均具备该字体或支持真人头像。

## 继承与检查

视频配置按字段合并：内置默认 → 旧项目 defaults → 共享默认 → 外层到最近作用域 → 本次要求。项目只指定横屏，仍会继承帧率与字幕样式。语言继续沿用本次、最近配置、共享、旧项目、auto 的优先级。

分辨率是实际宽高，不是标签。H.264 yuv420p 要求正偶数像素，fps 为正整数。显式横竖屏和宽高必须一致。只改方向会交换现有宽高；正方形使用短边，从正方形改回横竖屏需明确宽高。只给宽高时自动判断方向。非法边界、非有限坐标和头像越界在准备产物前报错。

## Agent 调用

视频补丁文件只包含 video 内部字段，例如 `{"orientation":"landscape","resolution":{"width":1920,"height":1080}}`，不是完整配置或产物对象。

```text
setup --directory <scope> --output-language zh-CN --video-config-file <video-patch.json>
config show --directory <project>
config show --directory <project> --video-config-file <one-time-patch.json>
produce plan --directory <project> --video-config-file <one-time-patch.json>
storyboard prepare --script-file <script.json> --video-config-file <one-time-patch.json> --output <new-directory>
```

只有 setup 保存偏好；show、plan、prepare 的本次覆盖不修改默认值。无 feature 的 setup 不下载模型。显式 --profile-file 是本次完整输出规格，与 prepare 补丁参数互斥，并保留自身身份。旧的仅语言配置仍然可用。

## 工作流行为

1. 规划前解析语言和视频规格。
2. 新视觉工作流固定实际配置，并将匹配的规格传给 prepare。
3. 生成 output-profile.json，据此设计分镜、场景、字幕和头像避让。
4. 编译与渲染只使用制作包内固定的 profile，不在渲染中途随共享默认值变化。
5. 显式视频配置存在时，登记后的实际 profile 必须匹配计划才能 checkpoint。

实际格式改变后重新规划视觉分支，复用报告、稿件、配音和对齐，保留分镜表达意图，重新布局并导出新版本。素材可能需要记录新依赖，但适用文件可直接复用，无需重新生图。不匹配配置的旧视觉包不能被静默当成新格式。纯调研或纯配音任务不依赖视频规格。

旧计划没有规格快照仍可读取；旧包保留，不自动改写。完整导入包自带固定规格，若要应用默认要求，应先在新工作副本中调整并更新引用，再渲染。已登记版本保持不可变。

自动检查覆盖配置继承、校验、本次覆盖、profile 生成、计划失效和不匹配 checkpoint 拦截，不证明任意分辨率和样式的视觉质量。本次不重新合成配音，也不增加已验证硬件范围。
