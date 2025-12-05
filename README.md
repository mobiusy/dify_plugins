# Dify Plugin: http_request_stream
[中文版](./README.zh.md)

A plugin for sending HTTP requests and returning response content as a stream. It is especially suitable for integrating with HTTP services that support streaming output (such as SSE or chunked responses), and continuously emits the stream content to the Answer node in real time.

## Basic Info
- Author: mobiusy
- Version: 0.0.3
- Type: tool

## Feature Highlights

### Streaming Requests and Output
- Sends HTTP requests (supports GET/POST/PUT/DELETE/HEAD/PATCH) and reads streaming responses in real time
- Built-in SSE-compatible headers (Accept: text/event-stream / Connection: keep-alive / Cache-Control: no-cache)
- Continuously outputs streamed text to the Answer node as a variable named `stream_text`

### Request Body Support
- Supports an optional JSON request body (provided as a string), automatically parsed and sent with the request

### Robust Error Handling
- Validates URL format (must start with http:// or https://)
- Friendly error messages for non-2xx HTTP status codes
- Connection stage timeout control (5s connection timeout; no overall read timeout to avoid interrupting the stream)

## Installation and Quick Start

1. Install this plugin in Dify (via Marketplace or local package import)
2. Add the tool `http_request_stream` in a Workflow or Toolflow
3. In the Answer node, select "Streaming output" and reference the variable `stream_text` to display real-time content

> Note: This plugin does not require additional credential configuration.

## Usage Examples

### 1) GET request to fetch streaming data
```yaml
tool: http_request_stream
parameters:
  method: "GET"
  url: "https://httpbin.org/stream/10"
```

### 2) POST request with JSON body and streaming response
```yaml
tool: http_request_stream
parameters:
  method: "POST"
  url: "https://example.com/sse"
  body: "{\"query\": \"hello\", \"user_id\": 123}"
```

### 3) Display stream output in the Answer node
- Set the Answer node content to reference `{{stream_text}}`
- When the remote service keeps returning streaming text, the Answer node will keep updating the display

## Tool Reference

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `http_request_stream` | Sends an HTTP request and returns response text as a stream | `method` (options: GET/POST/PUT/DELETE/HEAD/PATCH), `url` (required), `body` (optional JSON string) |

### Parameter Details
- `method` (required, select): HTTP method, default `GET`
- `url` (required, string): Full request URL (must start with http:// or https://)
- `body` (optional, string): Request body in JSON string form (only provide when needed; must be valid JSON)

### Output Variable
- `stream_text`: Each streamed text fragment received by the tool is immediately emitted as this variable, which can be used for dynamic display in the Answer node

## Error Handling

- Empty or invalid URL: raises `httpx.InvalidURL`
- Non-2xx status code: raises `httpx.HTTPStatusError` with the status code
- JSON parsing failure: raises `ValueError` when `body` is not a valid JSON string
- Network errors or interruptions: catches and raises `httpx.HTTPError` or other exceptions to aid troubleshooting

## Limitations and Notes

- Only supports HTTP/HTTPS URLs
- The server must support streaming output (SSE or chunked responses) to continuously return content; otherwise, it may respond once and end
- Custom headers or authentication parameters are not supported in the current version; if needed, extend support in the tool logic
- `body` supports only JSON string format

## FAQ and Troubleshooting

1. "URL must start with http:// or https://": Ensure the URL prefix is correct
2. "HTTP Error: <status_code>": The server returned a non-2xx status code; check whether the API is functioning and whether parameters are correct
3. "body must be a valid JSON string.": `body` must be a valid JSON string; use double quotes and ensure it can be parsed
4. Long periods without output: The target endpoint may not support streaming, or output may be blocked by a gateway/proxy

## Development Notes

This plugin is built with the Dify plugin framework and follows the "one file, one tool class" best practice:
- Tool definition: `tools/http_request_stream.yaml`
- Tool implementation: `tools/http_request_stream.py` (class name: `HttpRequestStreamTool`)
- Provider configuration: `provider/http_request_stream.yaml`; this plugin currently does not require credentials

Implementation highlights:
- Uses `httpx.stream` for streaming reads and sets SSE-compatible headers
- Each line of streamed text is emitted via `create_stream_variable_message("stream_text", line)`

## License

This plugin is provided as-is for use with Dify. Refer to Dify's license terms for details on usage rights.
