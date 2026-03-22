# IP Theme Asset Guide

This folder is only for frontend theme visuals used by the redesigned pages.
Do not put character avatars or character stands here.

## Frontend vs backend split

### Frontend theme assets

Put these in `AnimeSpeechGen/src/assets/ip-themes`:

- home carousel images
- IP logos and title lockups
- page backgrounds
- UI ornaments and borders
- glow, mist, particle, and other decorative effects
- reusable textures

### Backend character assets

Put these in `AniVoiceBackend/static`:

- character avatars
  - `AniVoiceBackend/static/character_avator/<Belong>/`
- character stand images
  - `AniVoiceBackend/static/stands/<Belong>/`
- any resource returned by `/get_belong_statics`

This matches the current backend code path, so no backend code changes are required for normal character additions.

## Directory map

### `shared`

- `shared/textures`
  - Reusable textures such as paper grain, star dust, mist, sparkle noise.
  - Recommended format: `webp` or transparent `png`.
  - Recommended size: `1024x1024` seamless textures, or `1920x1080` full-screen overlays.

- `shared/ui`
  - Reusable decorative UI parts such as borders, masks, ribbons, light frames.
  - Recommended format: transparent `png` or `svg`.
  - Recommended size: long edge `512px` to `2048px`.

### `genshin/home`

- `genshin/home/carousel`
  - Hero carousel images for the search home first screen.
  - Use these for featured IP slides, weekly updates, and recommendation slides.
  - Recommended format: `webp` first, `jpg/png` acceptable.
  - Recommended size: desktop `1920x1080`; minimum `1600x900`.
  - Safe area: keep key subjects in the center `70%` width and middle `70%` height.

- `genshin/home/logos`
  - IP logo, event logo, or title lockup for carousel and entry cards.
  - Recommended format: transparent `png` or `svg`.
  - Recommended size: width `600px` to `1200px`.

### `genshin/voice`

- `genshin/voice/backgrounds`
  - Full-screen or large-panel backgrounds for the voice generation stage.
  - Recommended format: `webp` or `jpg`.
  - Recommended size: `1920x1080`; minimum `1600x900`.

- `genshin/voice/ornaments`
  - Decorative overlays such as elemental sigils, borders, frame corners, and panel trims.
  - Recommended format: transparent `png` or `svg`.
  - Recommended size: long edge `512px` to `1600px`.

- `genshin/voice/effects`
  - Glow, mist, particle strip, gradient bloom, wave ring, and spotlight overlays.
  - Recommended format: transparent `png`.
  - Recommended size: common variants `512x512`, `1024x1024`, or `1920x1080`.

## Backend character asset specs

These are not stored here, but this is the recommended size for the current backend-driven character pipeline.

- `AniVoiceBackend/static/character_avator/GenShin`
  - square `png/webp`
  - recommended `512x512`
  - minimum `256x256`

- `AniVoiceBackend/static/stands/GenShin`
  - transparent `png/webp`
  - recommended long edge `1800px` to `2600px`
  - minimum `1400px`

## Suggested naming

- Use stable character keys for backend character files so avatar and stand names can match.
- Use lowercase kebab-case for frontend theme assets.
- Examples:
  - frontend: `carousel-main.webp`
  - frontend: `weekly-update.webp`
  - frontend: `genshin-logo.png`
  - backend: `Ayaka.png`
  - backend: `YaeMiko.png`

## Minimum delivery set for the first implementation

- Frontend
  - `genshin/home/carousel`: 2 to 3 hero slide images
  - `genshin/home/logos`: 1 main Genshin logo
  - `genshin/voice/backgrounds`: 1 main voice-stage background
  - `genshin/voice/ornaments`: 2 to 4 decorative overlays

- Backend
  - `static/character_avator/GenShin`: 6 to 8 character avatars
  - `static/stands/GenShin`: 6 to 8 matching stand images

## Notes

- Prefer `webp` for large frontend raster images to reduce bundle size.
- Prefer transparent `png` for stand images and overlay effects.
- Do not mix banner, ornament, and character resources in the backend `stands` or `character_avator` folders.
