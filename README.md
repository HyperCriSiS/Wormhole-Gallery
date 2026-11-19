<p align="center"><img src="icons/icon-128.png" alt="Wormhole icon" width="128"></p>

# Wormhole Gallery

**Ready-made picture sets for the Wormhole theme for Firefox and Waterfox.**

[![CI](https://github.com/HyperCriSiS/Wormhole-Gallery/actions/workflows/ci.yml/badge.svg)](https://github.com/HyperCriSiS/Wormhole-Gallery/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/HyperCriSiS/Wormhole-Gallery)](LICENSE)

Each set is one picture made for [Wormhole](https://github.com/HyperCriSiS/Firefox-Theme-Wormhole):
its top strip runs behind tabs and toolbars, the rest fills the new tab page,
and three matching colors tint menus, the address bar and the selected tab.

## 📦 Installation

1. Install [Wormhole](https://github.com/HyperCriSiS/Firefox-Theme-Wormhole/releases/latest).
2. Pick a set below and open its release ([all releases](https://github.com/HyperCriSiS/Wormhole-Gallery/releases)).
   Download `<id>-header.jpg` and `<id>-wallpaper.jpg`.
3. In the Wormhole settings, upload them as header image and new tab background,
   and enter the three colors from [index.json](index.json), or press
   **Suggest colors from the images**.

## ✨ Features

- Dark and light sets, tagged by subject, genre, time of day, season, mood,
  color and style ([tag list](tools/tags.json)).
- Every set keeps the left edge calm for a sidebar and the area behind the tab
  titles readable.
- Checked in Firefox and Waterfox (Photon, Proton and Nova), with and without a
  sidebar.

## 🖼️ Screenshots

<!-- sets:start -->
<table>
<tr><td><a href="previews/storm-over-the-sea.jpg"><img src="previews/storm-over-the-sea.jpg" width="260" alt="Storm Over the Sea"></a><br><b>Storm Over the Sea</b><br><code>storm-over-the-sea</code></td><td><a href="previews/pine-forest-in-morning-fog.jpg"><img src="previews/pine-forest-in-morning-fog.jpg" width="260" alt="Pine Forest in Morning Fog"></a><br><b>Pine Forest in Morning Fog</b><br><code>pine-forest-in-morning-fog</code></td><td><a href="previews/manta-in-sunlight.jpg"><img src="previews/manta-in-sunlight.jpg" width="260" alt="Manta in Sunlight"></a><br><b>Manta in Sunlight</b><br><code>manta-in-sunlight</code></td></tr>
<tr><td><a href="previews/dj-on-a-tropical-beach.jpg"><img src="previews/dj-on-a-tropical-beach.jpg" width="260" alt="DJ on a Tropical Beach"></a><br><b>DJ on a Tropical Beach</b><br><code>dj-on-a-tropical-beach</code></td><td><a href="previews/caravan-under-the-milky-way.jpg"><img src="previews/caravan-under-the-milky-way.jpg" width="260" alt="Caravan Under the Milky Way"></a><br><b>Caravan Under the Milky Way</b><br><code>caravan-under-the-milky-way</code></td></tr>
</table>

5 sets; the newest 5 are shown. Browse all of them in the add-on or in [index.json](index.json).
<!-- sets:end -->

## ⚙️ Configuration

Each entry in [index.json](index.json) describes one set:

| Field | Meaning |
|---|---|
| `id` | Stable name; the image files are `<id>-header.jpg` and `<id>-wallpaper.jpg` |
| `title` | Display name |
| `category` | One of the categories in [tools/tags.json](tools/tags.json), for example `sci-fi` |
| `style` | The set's style tag, for example `photorealistic` |
| `release` | Release that holds the images, for example `batch-001` |
| `tags` | Tags from [tools/tags.json](tools/tags.json), including `dark` or `light` |
| `colors` | `bottom`, `menu` and `accent` for the Wormhole settings |
| `preview` | Small preview image in this repository |

## 🛠️ Adding sets

New pictures go to `inbox/batch-NNN/` (ignored by git), one image and one JSON
file per set with `schema`, `id`, `title`, `category`, `tags` and `colors`. Then:

```bash
python tools/pipeline.py inbox/batch-002 --batch batch-002 --upscaler path/to/realesrgan-ncnn-vulkan.exe --upload
```

The pipeline upscales each picture to 3840 px with
[Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) and the digital-art-4x
model, checks the safe areas, cuts header and wallpaper, uploads them to the
release and updates `index.json`, the previews and the grid above.

## 📄 License

GNU Affero General Public License v3.0 only. See [LICENSE](LICENSE).
