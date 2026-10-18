"""Human-readable export labels. Artifact prose is always authored by the agent."""
from pathlib import Path
from string import Formatter
from .common import CastError, read_json
from .config import language_tag

ZH = {
    'As of': '资料截至', 'Audience': '受众', 'Scope': '范围',
    'This report is incomplete; evidence gaps are listed below. Not all conclusions are verified.': '这份报告资料尚不完整，证据缺口见下文；暂不能把其中所有判断当作已核实事实。',
    'Limitations': '结论的适用范围', 'Conflicting sources': '资料分歧', 'Open questions': '还不能确定的事',
    'Sources and access': '来源与读取情况', 'Not retained': '未留存',
    'Full text read': '已读全文', 'Relevant excerpt read': '已读相关片段', 'Metadata only': '仅元数据',
    'Unavailable': '无法读取', 'Accessed': '访问', 'Published': '发布日期', 'Unknown': '未知',
    'Narration script': '口播稿',
    'Estimated length: {seconds} seconds at an assumed rate; the actual duration depends on synthesized audio.': '篇幅估算约 {seconds} 秒，仅按假定速度计算；实际时长以配音为准。',
    'Target duration: {seconds} seconds.': '目标时长：{seconds} 秒。',
    'External source; facts have not been independently verified.': '输入为外部报告，事实尚未独立核验。',
    'The source report is incomplete and has evidence gaps.': '来源报告资料不完整，仍有证据缺口。',
    'Batch production report': '批量制作报告',
    'Completed {done} / {total} projects; batch state: {state}.': '已完成 {done} / {total} 个项目；批次状态：{state}。',
    '| Project | Status | Artifact | Notes |': '| 项目 | 状态 | 产物 | 说明 |', 'View': '查看',
    'pending': '待执行', 'active': '处理中', 'succeeded': '已完成', 'failed': '失败',
    'needs_input': '需补充信息', 'needs_replan': '需重新规划', 'cancelled': '已取消',
    'The queue was cancelled with active items; inspect and stop their actual tasks.': '队列已取消，仍有运行中项目；需要核对并停止其实际任务。',
    'Video storyboard review': '视频分镜审阅稿',
    'Narration is preserved; the following links content to actual audio timing.': '口播正文保持既有配音，以下是内容与实际时间的关联。',
    'Time': '时间', 'Narration': '口播', 'Screen': '屏幕', 'Animation anchors': '动画锚点',
    '{seconds} s: {target}, anchored to "{quote}"': '{seconds} 秒：{target}，绑定“{quote}”',
}


def labels(language, directory=None):
    tag = language_tag(language)
    if tag == 'auto':
        raise CastError('unresolved_language', 'The agent must resolve auto and record a concrete artifact language before export.')
    if tag.lower() in ('zh', 'zh-cn', 'zh-hans', 'zh-hans-cn'):
        mapping = ZH
    elif tag.split('-')[0] == 'en':
        mapping = {}
    else:
        start = Path(directory or Path.cwd()).resolve()
        if start.is_file():
            start = start.parent
        candidates = [p / '.codoop-cast/locales' / (tag + '.json') for p in (start, *start.parents)]
        path = next((p for p in candidates if p.is_file()), None)
        if path is None:
            raise CastError('missing_locale', 'Have the agent translate the English label keys from castlib/locale.py into .codoop-cast/locales/' + tag + '.json before export.')
        mapping = read_json(path)
        if not isinstance(mapping, dict) or not all(isinstance(mapping.get(k), str) and mapping[k].strip() for k in ZH):
            raise CastError('invalid_locale', 'The locale must provide a nonempty string for every English label key.')
        try:
            fields = lambda text: sorted((field, spec, conversion) for _, field, spec, conversion in Formatter().parse(text) if field is not None)
            if any(fields(key) != fields(mapping[key]) for key in ZH):
                raise ValueError('Changed formatting placeholders')
        except ValueError as exc:
            raise CastError('invalid_locale', 'Preserve all label formatting placeholders: ' + str(exc)) from exc
    return lambda key: mapping.get(key, key)
