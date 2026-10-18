# Skill 命名规范

[English](../en/30-skill-naming.md) | [简体中文](30-skill-naming.md)

公开入口与 [codoop-flow](https://github.com/Codoop/codoop-flow/tree/main/skills) 对齐，采用 `codoop-<功能>`，不重复插件产品名。插件仍叫 `codoop-cast`，运行时目录、共享数据、CLI 命令和项目格式不变。

| 原名称 | 新名称 |
| --- | --- |
| codoop-cast-setup | codoop-setup |
| codoop-cast-research | codoop-research |
| codoop-cast-script | codoop-script |
| codoop-cast-voice | codoop-voice |
| codoop-cast-subtitles | codoop-subtitles |
| codoop-cast-storyboard | codoop-storyboard |
| codoop-cast-assets | codoop-assets |
| codoop-cast-scenes | codoop-scenes |
| codoop-cast-video | codoop-video |
| codoop-cast-produce | codoop-produce |

初始化使用 `codoop-setup`，不占用 codoop-flow 已有的 `codoop-init`。目录、SKILL.md 的 name、默认提示词调用、展示名称、交叉引用及新工作流统一使用新名称。Skill 文档继续保持英文。

备用安装用户重新运行安装器即可发现新名称。成功安装后，只移除指向本插件自身 bundle 的旧发现符号链接；保留其他插件、无关路径、旧 bundle 代码、声音、任务和内容项目。如果新名称已被其他 skill 占用，在复制前停止，不覆盖。原生插件用户通过宿主更新，并按宿主支持的方式刷新发现。

旧工作流计划保持原文与哈希不变；运行时返回下一步时，按环节路由到当前公开 skill 名称。这是兼容路由，不改写历史文件，也不额外保留一套重复的旧 skill。
