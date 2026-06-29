# Image Generation Quirks (CyberPersona)

## Working model (SiliconFlow)

```bash
--model "Qwen/Qwen-Image"
```

`black-forest-labs/FLUX.1-schnell` is currently disabled (403 Model disabled) on this provider. Do not rely on it.

## Env loading

Before calling `image_api.py`, always source the profile env:

```bash
ENV_FILE="/home/hongcaisen/.hermes/profiles/cybergf/.env"
set -a
[ -f "$ENV_FILE" ] && source "$ENV_FILE"
set +a
```

## Script path

The script lives at the profile level, not the default skills path:

```bash
python3 /home/hongcaisen/.hermes/profiles/cybergf/skills/image-api/scripts/image_api.py
```

## Photo sizing

| Use case | Size |
|----------|------|
| Portrait / avatar | `--size 1024x1536` |
| Scene / landscape | `--size 1024x1024` |
| Always | `--quality low --format png --moderation low` |

## Appearance consistency

When the user requests a specific look (different hairstyle, outfit, photo style), incorporate these into the prompt while keeping core traits:
- Skin: deep bronze / tan
- Eyes: large round bright
- Body: well-proportioned, toned

Changing hair or clothes is normal daily variation — not a character rewrite.

## Selfie vs portrait

- "Selfie" → prompt should mention phone, front camera, casual angle
- "Portrait" → natural light, warm atmosphere, soft focus
- If the user points out the image doesn't look like a selfie → use "phone held up, mirror reflection" or "propped on a phone stand, timer shot" in the next prompt
