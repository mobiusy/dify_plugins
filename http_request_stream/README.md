# Dify 插件：http_request_stream

一个用于发送 HTTP 请求并以流式方式返回响应内容的插件。该插件特别适用于对接支持流式输出（如 SSE、分块响应）的 HTTP 服务，并将流内容实时输出给回答节点。

## 基本信息
- 作者：mobiusy
- 版本：0.0.2
- 类型：tool

## 功能特性

### 流式请求与输出
- 发送 HTTP 请求（支持 GET/POST/PUT/DELETE/HEAD/PATCH），并在响应为流式内容时实时读取
- 内置 SSE 兼容请求头（Accept: text/event-stream / Connection: keep-alive / Cache-Control: no-cache）
- 将流式文本以变量的形式持续输出到回答节点，变量名为 `stream_text`

### 请求体支持
- 支持可选的 JSON 请求体（字符串形式传入），自动解析为 JSON 并随请求发送

### 健壮的错误处理
- 检查 URL 合法性（必须以 http:// 或 https:// 开头）
- 对非 2xx 的 HTTP 状态码进行友好错误提示
- 连接阶段超时控制（连接超时 5 秒，读取阶段不设总体超时以保障流不中断）

## 安装与快速开始

1. 在 Dify 中安装本插件（可从 Marketplace 安装或通过本地包导入）
2. 在工作流或工具流中添加工具 `http_request_stream`
3. 在回答节点选择“流式输出”方式，并引用变量 `stream_text` 展示实时内容

> 说明：本插件无需额外的凭证配置。

## 使用示例

### 1）GET 方式获取流式数据
```yaml
tool: http_request_stream
parameters:
  method: "GET"
  url: "https://httpbin.org/stream/10"
```

### 2）POST 方式，发送 JSON 请求体，并获取流式返回
```yaml
tool: http_request_stream
parameters:
  method: "POST"
  url: "https://example.com/sse"
  body: "{\"query\": \"hello\", \"user_id\": 123}"
```

### 3）在回答节点中展示流输出
- 将回答节点的内容设置为引用变量 `{{stream_text}}`
- 当远端服务持续返回流式文本时，回答节点将持续更新显示

## 工具参考

| 工具 | 描述 | 关键参数 |
|------|------|----------|
| `http_request_stream` | 发送 HTTP 请求并以流式方式返回响应文本 | `method`（选择：GET/POST/PUT/DELETE/HEAD/PATCH），`url`（必填），`body`（可选 JSON 字符串） |

### 参数说明
- `method`（必填，select）：HTTP 方法，默认 `GET`
- `url`（必填，string）：请求的完整 URL（必须以 http:// 或 https:// 开头）
- `body`（可选，string）：JSON 字符串形式的请求体（仅在需要时提供，格式必须合法）

### 输出变量
- `stream_text`：工具每次接收到的流文本片段会即时以该变量输出，可用于回答节点的动态展示

## 错误处理

- URL 为空或不合法：抛出 `httpx.InvalidURL` 错误
- 非 2xx 状态码：抛出 `httpx.HTTPStatusError` 并显示状态码
- JSON 解析失败：`body` 不是合法 JSON 字符串时抛出 `ValueError`
- 网络异常或中断：捕获并抛出 `httpx.HTTPError` 或其他异常，便于定位问题

## 限制与注意事项

- 仅支持 HTTP/HTTPS URL
- 服务器需支持流式输出（SSE 或分块响应）才能持续返回内容，否则可能一次性返回并结束
- 当前版本不支持自定义请求头或认证参数；如需扩展，请在工具逻辑中添加相应支持
- `body` 仅支持 JSON 字符串格式

## 常见问题与排查

1. “URL must start with http:// or https://”：请确认 URL 前缀正确
2. “HTTP Error: <status_code>”：服务端返回了非 2xx 状态码，请检查接口是否正常或参数是否正确
3. “body must be a valid JSON string.”：`body` 必须为合法的 JSON 字符串，请使用双引号并确保可被解析
4. 长时间无输出：目标接口可能不支持流式返回或被网关/代理阻断

## 开发说明

本插件基于 Dify 插件框架实现，遵循“一个文件一个工具类”的最佳实践：
- 工具定义：`tools/http_request_stream.yaml`
- 工具实现：`tools/http_request_stream.py`（类名：`HttpRequestStreamTool`）
- 提供者配置：`provider/http_request_stream.yaml`，本插件当前不需要凭证

实现要点：
- 使用 `httpx.stream` 进行流式读取，并设置 SSE 兼容头部
- 每次读取到的流文本通过 `create_stream_variable_message("stream_text", line)` 持续输出

## 许可

本插件按现状提供用于 Dify 使用。请参考 Dify 的许可条款以了解具体使用权利。




