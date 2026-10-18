# 字幕为什么需要时间轴

资料截至：2026-10-17 · 受众：第一次制作知识口播视频的用户

范围：用 WebVTT 的字幕条目说明时间轴的作用；不比较自动对齐模型，也不讨论平台投稿规则。

字幕需要知道什么时候出现、什么时候消失。以 WebVTT 为例，每条字幕除了文字，还包含开始和结束时间。 [MDN：WebVTT API](<https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API>)

## 把字幕理解成一张带时间的提示卡

你可以把一条字幕理解成一张提示卡：卡片上写着要显示的文字，也写着开始和结束时间。WebVTT 用这样的条目把文本与音视频时间联系起来。 [MDN：WebVTT API](<https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API>)

## 换了配音，为什么要重新核对

由这个机制可以推得：如果新配音把某句话挪到了不同的时间，旧字幕还在原来的时刻出现，就可能提前或延后。因此，配音改变后应重新核对字幕时间；文字一样，也不代表旧时间仍然合适。 [MDN：WebVTT API](<https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API>)

## 结论的适用范围

- 这里以 WebVTT 为例，没有逐一核对所有字幕文件格式。
- 这是根据字幕显示机制的推论，不是自动对齐准确率的实测结果。

## 还不能确定的事

- 自动对齐工具对这段配音到底有多准确？ 本报告没有做工具实测，制作视频时仍需听看检查。

## 来源与读取情况

- MDN：WebVTT API；已读相关片段；访问：2026-10-17；发布日期：未知；https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API；读取了定义和 Concepts and usage 的相关段落；仅留存简短中文转述，不是全文存档，发布日期未知。
