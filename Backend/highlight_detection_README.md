# highlight_detection_README.md

## Highlight Detection Module: Documentation, Comparison, and Future Enhancements

## Approach (Option 1: Heuristic-Based)

- Fetch chat logs and VODs automatically (Twitch API, Streamlink, VodBot).
- Analyze chat logs for message rate and emote bursts (pandas/numpy).
- Analyze audio for peaks (FFmpeg, robust detection).
- Output highlights.json with highlight timestamps.

## Detailed Comparison of Approaches

### Option 1: Heuristic-Based Detection (Current)

- Fast, simple, robust. No ML dependencies. Easy to tune and extend.
- May miss subtle highlights (e.g., visual gags, clutch plays with low chat/audio).

### Option 2: Multi-Modal ML-Based Detection (ArtKulak/DSCIG)

- Combines chat spikes, audio peaks, and video scene changes.
- Uses a lightweight ML model trained on labeled highlights.
- More accurate, can learn complex highlight patterns. Adaptable to new games or streamer styles.
- Requires labeled data and model training. More dependencies (PyTorch/TensorFlow). Slower to prototype.

### Option 3: Rule-Based + Game Event Hooks

- Uses Option 1 as a base, adds custom rules for game-specific events (e.g., Marvel Rivals voicelines, kill streaks).
- Can surface unique, brand-building moments. Requires ongoing rule updates for new games/events. More complex logic.

## Rationale for Current Approach

- Option 1 was chosen for rapid prototyping, reliability, and ease of integration.
- Future iterations can layer in Option 3 features (voiceline detection, custom rules) and explore Option 2 (ML) for improved accuracy.

## Limitations

- Chat logs may be missing for some VODs (Twitch API limitations).
- Audio peak detection may flag non-hype moments (background noise, music, etc.).
- Heuristic approach may miss subtle or visual-only highlights.

## Future Enhancements

- Add Marvel Rivals/game-specific event detection (voicelines, kill streaks, overlays).
- Integrate speech-to-text for streamer catchphrases or hype phrases.
- Add meme/reaction detection (face-cam, overlays, etc.).
- Explore ML-based highlight detection (ArtKulak, DSCIG, etc.).
- Tune thresholds and window sizes for best viral content results.
- Integrate highlight approval and rating feedback loop for continuous improvement.

## References

- ArtKulak’s Twitch Stream Highlights Detection (multi-modal, interpretable model)
- DSCIG: Deep learning for Twitch highlights (chat+video features)
- ExCcitement Extractor (sports excitement curve)
- VodBot (VOD+chat download, slicing, batch export)
- StreamLighter/Hype (chat density for highlight triggers)

---

**All design decisions, issues, and enhancement ideas should be tracked here for future review and iteration.**
