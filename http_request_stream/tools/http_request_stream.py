from collections.abc import Generator
from typing import Any

import httpx
from json import loads
import re

# 导入 logging 和自定义处理器
import logging
from dify_plugin.config.logger_format import plugin_logger_handler

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

# 使用自定义处理器设置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(plugin_logger_handler)

class HttpRequestStreamTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """
        调用 HTTP 请求流工具。

        :param tool_parameters: 工具参数，包含 HTTP 请求的相关信息。
            - url: HTTP 请求的 URL。
        :return: 一个生成器，用于 yield 工具调用消息。
        """
        url = tool_parameters.get("url")
        method = tool_parameters.get("method", "GET")
        body = tool_parameters.get("body", None)
        headers_str = tool_parameters.get("headers", None)
        if not url:
            err_msg = "URL cannot be empty."
            logger.error(err_msg)
            raise httpx.InvalidURL(err_msg)
        
        if not url.startswith(("http://", "https://")):
            err_msg = "URL must start with http:// or https://."
            logger.error(err_msg)
            raise httpx.InvalidURL(err_msg)

        # 解析 headers 参数：支持用户以 JSON 对象字符串方式传入请求头
        user_headers: dict[str, Any] = {}
        if headers_str:
            try:
                parsed = loads(headers_str)
                if isinstance(parsed, dict):
                    user_headers = parsed
                else:
                    err_msg = "headers must be a JSON object string."
                    logger.error(err_msg)
                    raise ValueError(err_msg)
            except ValueError:
                # 用户传入的 headers 字符串不是合法 JSON 或不是对象
                err_msg = "headers must be a valid JSON object string."
                logger.error(err_msg)
                raise ValueError(err_msg)

        # 构造 httpx.stream 的参数，增加 SSE 兼容头部与超时设置
        stream_kwargs: dict[str, Any] = {
            "method": method,
            "url": url,
            # 读取不设整体超时，连接阶段限制为 5 秒，避免读超时中断流
            "timeout": httpx.Timeout(timeout=None, connect=5.0),
        }

        # 默认 SSE 兼容请求头，提升与代理/网关的兼容性
        default_headers: dict[str, str] = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        # 合并用户请求头，用户值覆盖默认值，确保所有值为字符串类型
        merged_headers: dict[str, str] = {
            **default_headers,
            **{str(k): str(v) for k, v in user_headers.items()}
        }
        stream_kwargs["headers"] = merged_headers

        if body:
            # 检查body是否是合法的json格式
            try:
                req_body = loads(body)
                stream_kwargs["json"] = req_body
            except ValueError:
                err_msg = "body must be a valid JSON string."
                logger.error(err_msg)
                raise ValueError(err_msg)

        try:
            # 标记是否已经提取并输出过 conversation_id，避免重复输出
            conversation_id_emitted = False
            # 预编译匹配 conversation_id 的正则表达式：匹配形如 conversation_id/xxxxx 的片段
            conversation_id_pattern = re.compile(r"\bconversation_id\/([^\s]+)")
            with httpx.stream(**stream_kwargs) as response:
                # 对非 2xx 状态码进行友好提示并终止流
                if response.status_code < 200 or response.status_code >= 300:
                    err_msg = f"HTTP Error: {response.status_code}"
                    logger.error(err_msg)
                    # 使用 httpx 内置的 raise_for_status 构造并抛出包含 request/response 的异常
                    response.raise_for_status()
                for raw_line in response.iter_lines():
                    if raw_line is None:
                        continue
                    line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                    line = line.strip()
                    if line.startswith("data:"):
                        line = line[5:].strip()
                    if line:
                        # 先检测是否包含 conversation_id 片段
                        match = conversation_id_pattern.search(line)
                        if match:
                            # 命中 conversation_id 片段的 chunk，不输出到 stream_text
                            if not conversation_id_emitted:
                                conversation_id_value = match.group(1)
                                # 输出一次 conversation_id 变量，供后续节点引用
                                yield self.create_variable_message("conversation_id", conversation_id_value)
                                conversation_id_emitted = True
                            # 跳过本次 chunk 的 stream_text 输出
                            continue
                        # 非 conversation_id 的 chunk，正常输出到 stream_text
                        yield self.create_stream_variable_message("stream_text", line)
            
        except httpx.HTTPError as e:
            # 捕获 httpx 的 HTTP 异常，并输出到用户侧
            err_msg = f"HTTP Error: {e}"
            logger.error(err_msg)
            raise e
        except Exception as e:
            # 捕获其他意料之外的异常，避免中断
            err_msg = f"Unexpected Error: {e}"
            logger.error(err_msg)
            raise e
