# repeat4print

Tile an image across a sheet of paper as a print-ready PDF, with thin cutting
guides between the copies.

## Install

```sh
uv sync            # dev, then run with: uv run repeat4print ...
uv tool install .  # or install the `repeat4print` command globally
```

## Usage

```sh
repeat4print halaadas.png                              # 51mm cells, packed on A3
repeat4print halaadas.png -p a4 -l -g 4x3 -o cards.pdf # A4 landscape, 4x3
repeat4print halaadas.png --cell-width 65              # bigger cells, fewer fit
repeat4print halaadas.png -g 3x6 --cell-width auto     # 3x6 stretched to the page
repeat4print halaadas.png --guide-length 5             # edge marks, not lines
```

Cells are 51mm wide by default and keep the image aspect ratio; `--cell-width`
or `--cell-height` moves the other side with it. The grid defaults to `auto`:
as many copies as fit, centered. Pin it with `-g COLSxROWS`, and with a pinned
grid `--cell-width auto` scales the cells up until they fill the page in one
direction. Paper is `a3`, `a4`, `a5`, `letter`, or `WIDTHxHEIGHT` in
millimetres, `-l` swaps it to landscape.

`repeat4print --help` lists everything.
