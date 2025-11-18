# Asset Catalog

This directory contains the app icons and menu bar status icons for Voice Assistant.

## Required Assets

### App Icon (AppIcon.appiconset)

Standard macOS app icon set with the following sizes:

- 16x16 (@1x, @2x)
- 32x32 (@1x, @2x)
- 128x128 (@1x, @2x)
- 256x256 (@1x, @2x)
- 512x512 (@1x, @2x)

**Design**: Microphone icon with blue gradient background

### Menu Bar Icons

The app uses SF Symbols for menu bar status icons, so no custom images needed:

- **Idle**: `mic.fill` (system gray)
- **Listening**: `waveform` (system blue)
- **Processing**: `hourglass` (system orange)
- **Error**: `exclamationmark.triangle.fill` (system red)

## Asset Catalog Structure

```
Assets.xcassets/
├── AppIcon.appiconset/
│   ├── Contents.json
│   ├── icon_16x16.png
│   ├── icon_16x16@2x.png
│   ├── icon_32x32.png
│   ├── icon_32x32@2x.png
│   ├── icon_128x128.png
│   ├── icon_128x128@2x.png
│   ├── icon_256x256.png
│   ├── icon_256x256@2x.png
│   ├── icon_512x512.png
│   └── icon_512x512@2x.png
└── Contents.json
```

## Creating the App Icon

You can create the app icon using:

1. **Design the icon** (use Sketch, Figma, or Affinity Designer)
   - Start with 1024x1024 canvas
   - Design a microphone icon with blue gradient
   - Export as PNG with transparency

2. **Generate icon sizes** using one of these tools:
   - Icon Set Creator (Mac App Store)
   - https://appicon.co
   - ImageMagick script (see below)

### ImageMagick Script

```bash
#!/bin/bash
# Generate all icon sizes from 1024x1024 source

SOURCE="icon_1024x1024.png"
ICONSET="AppIcon.appiconset"

mkdir -p "$ICONSET"

# Generate each size
sips -z 16 16     "$SOURCE" --out "$ICONSET/icon_16x16.png"
sips -z 32 32     "$SOURCE" --out "$ICONSET/icon_16x16@2x.png"
sips -z 32 32     "$SOURCE" --out "$ICONSET/icon_32x32.png"
sips -z 64 64     "$SOURCE" --out "$ICONSET/icon_32x32@2x.png"
sips -z 128 128   "$SOURCE" --out "$ICONSET/icon_128x128.png"
sips -z 256 256   "$SOURCE" --out "$ICONSET/icon_128x128@2x.png"
sips -z 256 256   "$SOURCE" --out "$ICONSET/icon_256x256.png"
sips -z 512 512   "$SOURCE" --out "$ICONSET/icon_256x256@2x.png"
sips -z 512 512   "$SOURCE" --out "$ICONSET/icon_512x512.png"
sips -z 1024 1024 "$SOURCE" --out "$ICONSET/icon_512x512@2x.png"
```

## Contents.json Template

### AppIcon.appiconset/Contents.json

```json
{
  "images" : [
    {
      "filename" : "icon_16x16.png",
      "idiom" : "mac",
      "scale" : "1x",
      "size" : "16x16"
    },
    {
      "filename" : "icon_16x16@2x.png",
      "idiom" : "mac",
      "scale" : "2x",
      "size" : "16x16"
    },
    {
      "filename" : "icon_32x32.png",
      "idiom" : "mac",
      "scale" : "1x",
      "size" : "32x32"
    },
    {
      "filename" : "icon_32x32@2x.png",
      "idiom" : "mac",
      "scale" : "2x",
      "size" : "32x32"
    },
    {
      "filename" : "icon_128x128.png",
      "idiom" : "mac",
      "scale" : "1x",
      "size" : "128x128"
    },
    {
      "filename" : "icon_128x128@2x.png",
      "idiom" : "mac",
      "scale" : "2x",
      "size" : "128x128"
    },
    {
      "filename" : "icon_256x256.png",
      "idiom" : "mac",
      "scale" : "1x",
      "size" : "256x256"
    },
    {
      "filename" : "icon_256x256@2x.png",
      "idiom" : "mac",
      "scale" : "2x",
      "size" : "256x256"
    },
    {
      "filename" : "icon_512x512.png",
      "idiom" : "mac",
      "scale" : "1x",
      "size" : "512x512"
    },
    {
      "filename" : "icon_512x512@2x.png",
      "idiom" : "mac",
      "scale" : "2x",
      "size" : "512x512"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  }
}
```

## Design Guidelines

### App Icon Design

- **Style**: Modern, minimal, flat design
- **Primary Color**: Blue (#007AFF - Apple system blue)
- **Icon**: Microphone symbol
- **Background**: Subtle gradient or solid color
- **Padding**: Leave 10% padding around edges
- **Corner Radius**: macOS will apply automatically

### Example Design Concepts

1. **Concept 1**: Blue microphone on light background
   - Background: #F0F0F0
   - Microphone: #007AFF gradient to #5856D6

2. **Concept 2**: White microphone on blue background
   - Background: #007AFF gradient to #5856D6
   - Microphone: #FFFFFF

3. **Concept 3**: Minimalist microphone outline
   - Background: Transparent or white
   - Microphone: Blue outline (#007AFF), 3pt stroke

## Testing

After adding icons to the asset catalog:

1. Clean build folder (⇧⌘K in Xcode)
2. Build and run (⌘R)
3. Check menu bar and About window for icon appearance
4. Test on both Retina and non-Retina displays

## Notes

- Asset catalog is compiled to Assets.car at build time
- All images should be PNG with transparency
- Use sRGB color space
- Avoid text in icons (doesn't scale well)
- Test visibility on both light and dark menu bars
