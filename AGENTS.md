# Agent notes

- Language for code, comments, docs, titles and tags: American English.
- Only small files live in git: `index.json`, `previews/`, `tools/`. Full images
  are release assets (`batch-NNN`), never committed. `inbox/` and `out/` are ignored.
- A set id never changes once published: the add-on builds download links from
  `release` and `id`. Fix a broken image by uploading it again with `--clobber`.
- Tags come only from `tools/tags.json`. Adding a tag means editing that file.

## README style

- Centered icon on top, title, bold tagline, one badge row (at most six).
- Every `##` heading starts with an emoji. Fixed ones: ✨ Features,
  📦 Installation, 🚀 Usage, ⚙️ Configuration, 🖼️ Screenshots,
  🩺 Troubleshooting, 💬 Support, 🙏 Credits, 📄 License. Other sections get
  a fitting emoji of their own, never one twice per file.
- Install path first, features as bullets, configuration as a table, one
  screenshot when there is a UI, GitHub alerts for warnings.

## Verified for real

A change counts as checked only when:

1. `python tools/validate.py` passes.
2. New sets were loaded in Firefox or Waterfox with the Wormhole add-on: dark and
   light sets, with and without a sidebar, in the Waterfox styles Photon,
   Proton and Nova.

## Branches and releases

- Default branch: `main`. Pull requests are squash merged.
- A change to the README alone is pushed straight to `main`, without a pull request.
- A new batch: run `tools/pipeline.py inbox/batch-NNN --batch batch-NNN --upscaler <path> --upload`,
  then open a pull request with the new `index.json` entries and previews.
