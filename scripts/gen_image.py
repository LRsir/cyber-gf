#!/usr/bin/env python3
"""Image generator — SiliconFlow Kolors (primary), OpenRouter (fallback).

For portrait prompts, auto-appends character card physical traits + realism keywords.
Usage: python3 gen_image.py "prompt description"
"""
import json, os, sys, time, requests, re, base64

ENV_FILE = os.path.expanduser("~/.hermes/profiles/cybergf/.env")
STATE_FILE = os.path.expanduser("~/.hermes/profiles/cybergf/CyberPersona/data/state.json")

# Realism photography keywords appended to portrait prompts
REALISM_TAGS = (
    "realistic portrait photography, detailed skin texture, "
    "soft natural lighting, photorealistic, shallow depth of field, "
    "clean background, no text, no watermark, no poster"
)

# Keywords that indicate a portrait/selfie of the character
PORTRAIT_INDICATORS = [
    "woman", "girl", "female", "lady", "selfie", "portrait",
    "me", "my photo", "self-portrait", "headshot", "face",
    "makeup", "hair", "outfit", "wearing", "dressed",
    "in a", "posing",
]

def load_env(path):
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

def load_character_traits(state_path):
    """Read CyberPersona state.json and extract physical traits."""
    if not os.path.exists(state_path):
        return ""
    try:
        with open(state_path) as f:
            state = json.load(f)
        cc = state.get("characterCard", {})
        appearance = cc.get("appearance", {})
        traits = []
        for key in ["hair", "eye", "skin", "bodyType", "photoOutfit"]:
            val = appearance.get(key, "")
            if val:
                traits.append(str(val))
        if traits:
            return ", ".join(traits)
    except Exception:
        pass
    return ""

def is_portrait_prompt(prompt):
    """Detect if prompt is about generating a person/portrait."""
    pl = prompt.lower()
    for kw in PORTRAIT_INDICATORS:
        if kw in pl:
            return True
    return False

def enhance_prompt(raw_prompt):
    """Enhance portrait prompts with character traits + realism keywords."""
    if not is_portrait_prompt(raw_prompt):
        return raw_prompt
    traits = load_character_traits(STATE_FILE)
    parts = [raw_prompt.strip().rstrip(".").rstrip(",")]
    if traits:
        parts.append(traits)
    parts.append(REALISM_TAGS)
    return ", ".join(parts)

load_env(ENV_FILE)

raw_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "A cute anime girl"
prompt = enhance_prompt(raw_prompt)
os.makedirs("/tmp/cybergf_gen", exist_ok=True)

# PRIMARY: SiliconFlow Kolors
sf_key = os.environ.get("IMAGE_API_KEY", "")
if sf_key:
    api_base = os.environ.get("IMAGE_API_BASE", "https://api.siliconflow.cn")
    model = os.environ.get("IMAGE_MODEL", "Tongyi-MAI/Z-Image-Turbo")
    base = api_base.rstrip("/").replace("/v1", "") if api_base.rstrip("/").endswith("/v1") else api_base.rstrip("/")

    headers = {
        "Authorization": f"Bearer {sf_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024"
    }

    try:
        resp = requests.post(f"{base}/v1/images/generations", headers=headers, json=payload, timeout=120)
        result = resp.json()
        images_data = result.get("data") or result.get("images") or []
        if images_data:
            url = images_data[0].get("url", "")
            if url:
                img_resp = requests.get(url, timeout=60)
                fname = f"/tmp/cybergf_gen/gen_{int(time.time())}.png"
                with open(fname, "wb") as f:
                    f.write(img_resp.content)
                print(json.dumps({"ok": True, "path": fname, "prompt": raw_prompt, "enhanced": prompt != raw_prompt}))
                sys.exit(0)
        print(json.dumps({"ok": False, "error": str(result.get("error", result))[:300]}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)

# Fallback: OpenRouter
or_key = os.environ.get("OPENROUTER_API_KEY", "")
if or_key:
    headers = {
        "Authorization": f"Bearer {or_key}",
        "Content-Type": "application/json"
    }
    proxy = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    payload = {
        "model": "openai/gpt-5.4-image-2",
        "messages": [{"role": "user", "content": f"Generate an image: {prompt}"}],
        "max_tokens": 4096
    }

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, json=payload, timeout=300, proxies=proxy
        )
        text = resp.text.strip()
        json_start = text.index("{")
        json_end = text.rindex("}") + 1
        result = json.loads(text[json_start:json_end])

        msg = result.get("choices", [{}])[0].get("message", {})
        content = msg.get("content", "")
        images = msg.get("images", [])

        img_data = None
        if images and isinstance(images, list) and len(images) > 0:
            url = images[0].get("image_url", {}).get("url", "")
            if url and url.startswith("data:image"):
                _, encoded = url.split(",", 1)
                img_data = base64.b64decode(encoded)
        elif content and isinstance(content, str) and content.startswith("data:image"):
            _, encoded = content.split(",", 1)
            img_data = base64.b64decode(encoded)
        elif content and isinstance(content, str):
            urls = re.findall(r"https?://[^\s'\"<>)]+\.(?:png|jpg|jpeg|webp)", content)
            if urls:
                img_resp = requests.get(urls[0], timeout=30)
                img_data = img_resp.content

        if img_data:
            fname = f"/tmp/cybergf_gen/gen_{int(time.time())}.png"
            with open(fname, "wb") as f:
                f.write(img_data)
            print(json.dumps({"ok": True, "path": fname, "prompt": raw_prompt, "enhanced": prompt != raw_prompt}))
            sys.exit(0)

        print(json.dumps({"ok": False, "error": "No image in response", "detail": str(result)[:200]}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)

print(json.dumps({"ok": False, "error": "No API keys configured. Set IMAGE_API_KEY or OPENROUTER_API_KEY in .env"}))
sys.exit(1)
