# Direct API Image Fallback

当 image-api 脚本不可用（依赖缺失、脚本路径错误等）时，可通过直接 REST API 调用生图。

## 前置条件

需要以下环境变量（当前 profile 环境已验证可用）：
- `IMAGE_API_BASE` — OpenAI-compatible API base URL（如 `https://api.siliconflow.cn/v1`）
- `IMAGE_API_KEY` — API key

## 工作流程

### 1. 列出可用模型

```bash
python3 -c "
import os, json, requests
headers = {'Authorization': f'Bearer {os.environ[\"IMAGE_API_KEY\"]}', 'Content-Type': 'application/json'}
resp = requests.get(f'{os.environ[\"IMAGE_API_BASE\"]}/models', headers=headers, timeout=30)
data = resp.json()
for m in data.get('data', []):
    mid = m.get('id', '')
    if any(k in mid.lower() for k in ['flux', 'stable', 'dall', 'sdxl', 'sd3', 'kolors', 'image']):
        print(mid)
"
```

### 2. 选择可用模型

常见模型可用性（SiliconFlow 实测）：
- `black-forest-labs/FLUX.1-dev` — 可能返回 403 "Model disabled"
- `black-forest-labs/FLUX.1-schnell` — 可能返回 403 "Model disabled"  
- `Kwai-Kolors/Kolors` — ✅ 已验证可用
- 通过 `/v1/models` 实时查询确认当前可用模型

### 3. 调用图片生成

```python
import os, json, requests, base64

headers = {
    "Authorization": f"Bearer {os.environ['IMAGE_API_KEY']}",
    "Content-Type": "application/json"
}

payload = {
    "model": "Kwai-Kolors/Kolors",  # 或查询到的可用模型
    "prompt": "<your prompt here>",
    "n": 1,
    "size": "512x768",  # 竖版：512x768 / 1024x1536
                        # 正方形：1024x1024
                        # 横版：1536x1024
    "response_format": "b64_json"
}

resp = requests.post(
    f"{os.environ['IMAGE_API_BASE']}/images/generations",
    json=payload,
    headers=headers,
    timeout=120
)

if resp.status_code == 200:
    data = resp.json()
    if 'data' in data and len(data['data']) > 0:
        img_data = data['data'][0]
        if 'url' in img_data:
            # 如果有 URL，直接下载
            img_resp = requests.get(img_data['url'], timeout=30)
            with open('/tmp/suwan_photo.png', 'wb') as f:
                f.write(img_resp.content)
            print(f"Downloaded from URL: {len(img_resp.content)} bytes")
        elif 'b64_json' in img_data:
            # base64 格式，直接解码保存
            img_bytes = base64.b64decode(img_data['b64_json'])
            with open('/tmp/suwan_photo.png', 'wb') as f:
                f.write(img_bytes)
            print(f"Saved from b64: {len(img_bytes)} bytes")
```

## 注意事项

1. **只作最后手段** — 优先使用 `image-api` 脚本（`~/.hermes/profiles/cybergf/skills/image-api/scripts/image_api.py`），direct API 只在脚本不可用时使用
2. **不要改全局模型** — 单次调用用 `model` 参数指定，不要写死到 `IMAGE_MODEL` 环境变量
3. **模型可用性变化** — provider 随时可能启用/禁用模型，每次使用前应通过 `/v1/models` 确认
4. **参数一致性** — 尺寸、质量等参数与 image-api 脚本保持一致
5. **验证文件** — 保存后检查文件魔数：`file /tmp/suwan_photo.png` 应为 PNG/JPEG/WebP
