#!/usr/bin/env python3
"""微信接口错误解释工具。"""

from __future__ import annotations

from typing import Any


ERROR_GUIDE: dict[int, dict[str, list[str] | str]] = {
    -1: {
        "reason": "微信系统繁忙或临时错误。",
        "likely_causes": ["平台短暂不可用", "网络抖动"],
        "next_steps": ["稍后重试", "保留当前 chain-report.json 供接续执行"],
    },
    40001: {
        "reason": "access_token 无效，通常是 AppSecret、AppID 或 token 状态问题。",
        "likely_causes": ["AppID/AppSecret 不匹配", "凭证已重置", "token 已失效"],
        "next_steps": ["重新检查 WECHAT_APPID 和 WECHAT_APPSECRET", "确认后台开发者配置未变更"],
    },
    40013: {
        "reason": "AppID 不合法。",
        "likely_causes": ["WECHAT_APPID 配错", "使用了非公众号 AppID"],
        "next_steps": ["在公众号后台复制 AppID", "重新设置本机环境变量"],
    },
    40014: {
        "reason": "access_token 不合法。",
        "likely_causes": ["token 过期", "AppSecret 变更后旧 token 未刷新"],
        "next_steps": ["重新获取 token", "重新执行当前步骤"],
    },
    40037: {
        "reason": "media_id 不合法。",
        "likely_causes": ["thumb_media_id 不是当前账号素材", "封面素材上传失败后使用了旧值"],
        "next_steps": ["重新执行 upload-thumb", "确认草稿 JSON 使用最新 thumb_media_id"],
    },
    40064: {
        "reason": "IP 不在公众号后台白名单。",
        "likely_causes": ["本机出口 IP 未配置", "网络环境切换导致出口 IP 变化"],
        "next_steps": ["在公众号后台配置当前出口 IP", "重新执行接口步骤"],
    },
    41001: {
        "reason": "缺少 access_token 参数。",
        "likely_causes": ["token 获取失败", "接口 URL 拼接异常"],
        "next_steps": ["先运行 check-config", "确认 WECHAT_APPSECRET 已配置"],
    },
    41005: {
        "reason": "缺少 media 数据。",
        "likely_causes": ["图片路径错误", "上传文件为空"],
        "next_steps": ["检查本地图片路径和文件大小", "重新生成素材清单"],
    },
    45009: {
        "reason": "接口调用频率超过限制。",
        "likely_causes": ["短时间重复上传或创建草稿", "多成员共用同一账号高频操作"],
        "next_steps": ["降低重试频率", "稍后从失败阶段接续"],
    },
    45029: {
        "reason": "接口调用频率过高。",
        "likely_causes": ["重复执行 --execute", "自动重试间隔过短"],
        "next_steps": ["停止重复执行", "等待限制恢复后接续"],
    },
    48001: {
        "reason": "接口权限不足。",
        "likely_causes": ["公众号未开通相关接口权限", "账号类型不支持草稿或素材接口"],
        "next_steps": ["检查公众号后台接口权限", "确认账号类型和认证状态"],
    },
    61500: {
        "reason": "日期格式或调度参数错误。",
        "likely_causes": ["发布时间字段格式不符合要求"],
        "next_steps": ["检查发布门禁文件中的时间字段", "本 skill 默认不自动正式发布"],
    },
}


def explain_wechat_error(error: dict[str, Any]) -> dict[str, Any]:
    code_raw = error.get("errcode")
    try:
        code = int(code_raw)
    except (TypeError, ValueError):
        code = 0
    guide = ERROR_GUIDE.get(code)
    if guide:
        return {
            "errcode": code_raw,
            "errmsg": error.get("errmsg", ""),
            "reason": guide["reason"],
            "likely_causes": guide["likely_causes"],
            "next_steps": guide["next_steps"],
        }
    return {
        "errcode": code_raw,
        "errmsg": error.get("errmsg", ""),
        "reason": "未内置该微信错误码解释。",
        "likely_causes": ["接口返回了未覆盖的错误码", "需要查看微信官方文档或后台提示"],
        "next_steps": ["保留完整接口回执", "不要重复执行真实发布动作", "根据 errcode 补充错误码规则"],
    }
