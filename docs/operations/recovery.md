# Recovery

Primary recovery cases:

- stale claim with no heartbeat
- missing repo path
- broken GitHub auth
- merge blocked by conflict
- duplicated or drifted labels/status metadata

Current recovery commands:

- `hermes doctor`
- `hermes preflight`
- `hermes state-inspect`
- `hermes reap-stale`

