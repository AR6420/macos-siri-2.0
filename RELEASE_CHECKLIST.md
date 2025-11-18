# Release Checklist for Voice Assistant

Complete checklist for preparing and releasing a new version of Voice Assistant.

## Pre-Release Checklist

### Version Planning

- [ ] Review milestone goals and completion status
- [ ] Verify all planned features are implemented
- [ ] Review and prioritize outstanding issues
- [ ] Decide on version number (SemVer: MAJOR.MINOR.PATCH)
  - MAJOR: Breaking changes
  - MINOR: New features, backwards compatible
  - PATCH: Bug fixes, backwards compatible

### Code Quality

- [ ] All unit tests passing
  ```bash
  cd python-service
  poetry run pytest
  ```

- [ ] All integration tests passing
  ```bash
  poetry run pytest tests/integration/
  ```

- [ ] Code coverage meets threshold (>80%)
  ```bash
  poetry run pytest --cov=voice_assistant --cov-report=html
  ```

- [ ] No critical linting errors
  ```bash
  poetry run ruff check .
  poetry run mypy src/
  ```

- [ ] Code formatted consistently
  ```bash
  poetry run black --check .
  poetry run isort --check .
  ```

- [ ] Swift code builds without warnings
  ```bash
  cd swift-app
  xcodebuild -scheme VoiceAssistant -configuration Release
  ```

### Documentation

- [ ] README.md is up to date
- [ ] CHANGELOG.md updated with all changes
- [ ] Version number updated in:
  - [ ] `VERSION` file
  - [ ] `python-service/pyproject.toml`
  - [ ] `swift-app/Info.plist`
  - [ ] CHANGELOG.md
- [ ] All new features documented in docs/
- [ ] API documentation updated
- [ ] Screenshots/demos are current
- [ ] INSTALLATION.md reviewed
- [ ] DEPLOYMENT.md reviewed
- [ ] TROUBLESHOOTING.md updated with new issues

### Dependencies

- [ ] Python dependencies up to date and locked
  ```bash
  poetry update
  poetry lock
  ```

- [ ] No security vulnerabilities
  ```bash
  poetry run safety check
  ```

- [ ] License compliance verified
  ```bash
  poetry run pip-licenses
  ```

- [ ] Whisper.cpp submodule updated (if needed)

### Testing

- [ ] Manual testing completed (see [Manual Testing](#manual-testing-checklist))
- [ ] Tested on clean macOS Tahoe 26.1 system
- [ ] Tested with Apple Silicon (M1/M2/M3)
- [ ] Tested with Intel Mac (if supported)
- [ ] All LLM backends tested:
  - [ ] Local gpt-oss:120b
  - [ ] OpenAI GPT-4/GPT-4o
  - [ ] Anthropic Claude
  - [ ] OpenRouter
- [ ] All automation tools tested
- [ ] Performance benchmarks meet targets
- [ ] Memory leaks checked (Instruments/Activity Monitor)
- [ ] Battery impact assessed (Energy Impact)

---

## Build Process

### 1. Prepare Repository

- [ ] Create release branch
  ```bash
  git checkout -b release/v1.0.0
  ```

- [ ] Update version numbers (see above)
- [ ] Update CHANGELOG.md
  - Move items from [Unreleased] to new version section
  - Add release date
  - Add GitHub compare link

- [ ] Commit version bump
  ```bash
  git add VERSION CHANGELOG.md python-service/pyproject.toml
  git commit -m "chore: bump version to 1.0.0"
  ```

- [ ] Push release branch
  ```bash
  git push origin release/v1.0.0
  ```

### 2. Build Artifacts

- [ ] Clean previous builds
  ```bash
  rm -rf dist/
  rm -rf swift-app/build/
  ```

- [ ] Setup whisper.cpp
  ```bash
  ./scripts/setup_whisper.sh
  ```

- [ ] Run build verification
  ```bash
  ./scripts/verify_build.sh
  ```
  - All checks should pass

- [ ] Build DMG installer
  ```bash
  ./scripts/build_dmg.sh
  ```
  - Verify: `dist/VoiceAssistant-1.0.0.dmg` created
  - Verify: SHA256 checksum generated
  - Verify: Build manifest created

- [ ] Build PKG installer
  ```bash
  ./scripts/build_pkg.sh
  ```
  - Verify: `dist/VoiceAssistant-1.0.0.pkg` created

- [ ] Test installers on clean system
  - [ ] DMG installs successfully
  - [ ] PKG installs successfully
  - [ ] App launches without errors
  - [ ] Permissions requested correctly
  - [ ] Basic functionality works

### 3. Code Signing & Notarization

#### Code Sign App

- [ ] Sign the app bundle
  ```bash
  codesign --deep --force --verify --verbose \
    --sign "Developer ID Application: Your Name (TEAM_ID)" \
    --options runtime \
    --entitlements swift-app/VoiceAssistant.entitlements \
    swift-app/build/Release/VoiceAssistant.app
  ```

- [ ] Verify signing
  ```bash
  codesign --verify --verbose=4 \
    swift-app/build/Release/VoiceAssistant.app
  spctl --assess --verbose=4 \
    swift-app/build/Release/VoiceAssistant.app
  ```

#### Notarize DMG

- [ ] Submit for notarization
  ```bash
  xcrun notarytool submit dist/VoiceAssistant-1.0.0.dmg \
    --keychain-profile "voice-assistant-notary" \
    --wait
  ```

- [ ] Staple notarization ticket
  ```bash
  xcrun stapler staple dist/VoiceAssistant-1.0.0.dmg
  ```

- [ ] Verify stapling
  ```bash
  xcrun stapler validate dist/VoiceAssistant-1.0.0.dmg
  ```

#### Sign & Notarize PKG

- [ ] Sign PKG
  ```bash
  productsign --sign "Developer ID Installer: Your Name (TEAM_ID)" \
    dist/VoiceAssistant-1.0.0.pkg \
    dist/VoiceAssistant-1.0.0-signed.pkg
  ```

- [ ] Notarize PKG
  ```bash
  xcrun notarytool submit dist/VoiceAssistant-1.0.0-signed.pkg \
    --keychain-profile "voice-assistant-notary" \
    --wait
  ```

- [ ] Staple PKG
  ```bash
  xcrun stapler staple dist/VoiceAssistant-1.0.0-signed.pkg
  ```

### 4. Final Verification

- [ ] Install from notarized DMG on clean system
- [ ] Verify no Gatekeeper warnings
- [ ] Test all core features
- [ ] Check Activity Monitor for issues
- [ ] Verify uninstaller works
- [ ] Run automated verification
  ```bash
  ./scripts/verify_build.sh
  ```

---

## Release Process

### 1. Create Git Tag

- [ ] Merge release branch to main
  ```bash
  git checkout main
  git merge release/v1.0.0
  ```

- [ ] Create annotated tag
  ```bash
  git tag -a v1.0.0 -m "Release version 1.0.0"
  ```

- [ ] Push tag
  ```bash
  git push origin v1.0.0
  ```

### 2. GitHub Release

- [ ] Go to GitHub → Releases → Draft a new release
- [ ] Choose tag: v1.0.0
- [ ] Release title: "Voice Assistant 1.0.0"
- [ ] Copy release notes from CHANGELOG.md
- [ ] Upload artifacts:
  - [ ] `VoiceAssistant-1.0.0.dmg`
  - [ ] `VoiceAssistant-1.0.0.dmg.sha256`
  - [ ] `VoiceAssistant-1.0.0-signed.pkg`
  - [ ] `VoiceAssistant-1.0.0-manifest.txt`
- [ ] Mark as pre-release (if beta)
- [ ] Publish release

### 3. Verify Release

- [ ] Download artifacts from GitHub Release
- [ ] Verify checksums
  ```bash
  shasum -a 256 -c VoiceAssistant-1.0.0.dmg.sha256
  ```
- [ ] Test installation from GitHub-hosted DMG
- [ ] Verify download counts updating

---

## Post-Release

### Update Documentation

- [ ] Update website with new version
- [ ] Update download links
- [ ] Add release announcement blog post
- [ ] Update documentation site
- [ ] Update README badges (if version badges used)

### Announcements

- [ ] Post on GitHub Discussions
- [ ] Tweet release announcement
- [ ] Post on Reddit (r/MacApps, r/opensource)
- [ ] Post on Hacker News (Show HN)
- [ ] Email mailing list subscribers
- [ ] Update Product Hunt (if listed)

### Monitoring

- [ ] Monitor GitHub Issues for bug reports
- [ ] Check download statistics
- [ ] Monitor user feedback
- [ ] Watch crash reports (if implemented)
- [ ] Review analytics (if implemented)

### Cleanup

- [ ] Delete release branch (after merge)
  ```bash
  git branch -d release/v1.0.0
  git push origin --delete release/v1.0.0
  ```
- [ ] Archive old build artifacts
- [ ] Update development branch
- [ ] Plan next milestone

---

## Manual Testing Checklist

### Installation Testing

- [ ] DMG mounts correctly
- [ ] App drags to Applications
- [ ] DMG ejects cleanly
- [ ] App launches from Applications
- [ ] PKG installs without errors
- [ ] Post-install scripts execute

### Permissions Testing

- [ ] Microphone permission requested
- [ ] Accessibility permission requested
- [ ] Input Monitoring permission requested
- [ ] Permissions persist after restart
- [ ] App handles denied permissions gracefully

### Wake Word Testing

- [ ] "Hey Claude" activates correctly
- [ ] False positive rate is acceptable
- [ ] Sensitivity adjustment works
- [ ] Works in noisy environment
- [ ] Works with different voices/accents

### Speech Recognition Testing

- [ ] Clear speech transcribed accurately
- [ ] Accented speech handled well
- [ ] Background noise filtered
- [ ] Long utterances captured
- [ ] Short commands work
- [ ] Different Whisper models selectable

### LLM Backend Testing

#### Local (gpt-oss:120b)
- [ ] Connects to local server
- [ ] Responses are coherent
- [ ] Streaming works (if enabled)
- [ ] Handles server disconnect

#### OpenAI
- [ ] API key validation
- [ ] Model selection works
- [ ] Rate limiting handled
- [ ] Error messages clear

#### Anthropic
- [ ] API key validation
- [ ] Model selection works
- [ ] Responses match quality expectations
- [ ] Error handling works

#### OpenRouter
- [ ] API key validation
- [ ] Multiple models selectable
- [ ] Routing works correctly

### Automation Tools Testing

- [ ] AppleScript execution works
- [ ] Application control via Accessibility API
- [ ] File operations (read/write/list)
- [ ] Web search returns results
- [ ] iMessage sending (with confirmation)
- [ ] System info queries

### UI Testing

- [ ] Menu bar icon displays
- [ ] Icon changes with states (idle/listening/processing)
- [ ] Preferences window opens
- [ ] All preferences save correctly
- [ ] Preferences persist after quit
- [ ] About window shows correct version
- [ ] Quit works correctly

### Performance Testing

- [ ] Idle CPU usage <5%
- [ ] Wake word detection latency <500ms
- [ ] STT latency <500ms (5s audio)
- [ ] Local LLM response <2s
- [ ] Cloud LLM response <5s
- [ ] Memory usage acceptable
- [ ] No memory leaks over time
- [ ] Battery impact acceptable

### Edge Cases

- [ ] Handles system sleep/wake
- [ ] Handles network disconnection
- [ ] Handles mic disconnection
- [ ] Handles full disk
- [ ] Handles API quota exceeded
- [ ] Handles malformed config
- [ ] Handles corrupted models
- [ ] Graceful degradation

### Uninstallation Testing

- [ ] Uninstaller runs without errors
- [ ] All files removed
- [ ] Preferences cleaned
- [ ] Keychain items removed
- [ ] Logs removed
- [ ] No orphaned processes

---

## Rollback Plan

If critical issues are discovered after release:

### Immediate Actions

1. **Add warning to release notes**
   - Edit GitHub Release
   - Add prominent warning at top
   - Describe issue and workaround

2. **Create hotfix branch**
   ```bash
   git checkout -b hotfix/v1.0.1 v1.0.0
   ```

3. **Fix critical issue**
   - Make minimal changes
   - Test thoroughly
   - Update CHANGELOG

4. **Release hotfix**
   ```bash
   git tag -a v1.0.1 -m "Hotfix for issue #123"
   git push origin v1.0.1
   ```

### If Unfixable Quickly

1. **Mark release as pre-release**
2. **Point users to previous stable version**
3. **Work on fix in development**
4. **Release new version when ready**

---

## Version-Specific Notes

### For Major Releases (X.0.0)

- [ ] Migration guide for breaking changes
- [ ] Deprecation warnings added in previous version
- [ ] Extra testing of upgrade path
- [ ] Communication plan for breaking changes

### For Minor Releases (X.Y.0)

- [ ] Feature announcement prepared
- [ ] Tutorial/demo for new features
- [ ] Documentation for new features

### For Patch Releases (X.Y.Z)

- [ ] Bug fix changelog clear
- [ ] Regression testing focused on fixed bugs
- [ ] Can be fast-tracked if critical

---

## Release Template

Use this template for GitHub Release notes:

```markdown
# Voice Assistant vX.Y.Z

[Brief description of release - major features or fixes]

## ✨ Highlights

- [Main feature 1]
- [Main feature 2]
- [Main fix]

## 📥 Installation

Download the DMG or PKG installer below:

**Recommended:** [VoiceAssistant-X.Y.Z.dmg](link)

**For MDM/Enterprise:** [VoiceAssistant-X.Y.Z.pkg](link)

**Checksum:** [VoiceAssistant-X.Y.Z.dmg.sha256](link)

## 📋 Full Changelog

[Copy from CHANGELOG.md]

## 🔒 Security

This release has been code signed and notarized by Apple.

SHA256: [checksum]

## 📖 Documentation

- [Installation Guide](link to INSTALLATION.md)
- [Usage Guide](link to docs/USAGE.md)
- [Troubleshooting](link to docs/TROUBLESHOOTING.md)

## 🐛 Known Issues

- [Issue 1 if any]
- [Issue 2 if any]

## 💬 Feedback

We'd love to hear from you! Please:
- [Open an issue](link) for bugs
- [Start a discussion](link) for questions
- [Contribute](link to CONTRIBUTING.md) improvements

## 🙏 Thanks

Thank you to all contributors who made this release possible!

[List of contributors if applicable]
```

---

## Emergency Contacts

**Build Issues:** @build-team
**Security Issues:** security@voiceassistant.dev
**Release Manager:** @release-manager

---

**Last Updated:** 2024-11-18
**Template Version:** 1.0.0
