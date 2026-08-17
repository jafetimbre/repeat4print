"""Tile an image across a sheet of paper, ready for printing and cutting."""

import argparse
import sys

from fpdf import FPDF
from PIL import Image

DEFAULT_CELL_WIDTH = 51.0

# Marks --cell-width as unset: the default only applies when --cell-height is
# left out too, and "auto" already means None.
UNSET = object()

PAPER_SIZES = {
    "a3": (297.0, 420.0),
    "a4": (210.0, 297.0),
    "a5": (148.0, 210.0),
    "letter": (215.9, 279.4),
}


def parse_paper(value):
    """Parse a paper spec: a named size, or "WIDTHxHEIGHT" in millimetres."""
    name = value.lower()
    if name in PAPER_SIZES:
        return PAPER_SIZES[name]
    try:
        width, height = (float(part) for part in name.split("x"))
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"unknown paper size {value!r}: use one of "
            f"{', '.join(sorted(PAPER_SIZES))}, or WIDTHxHEIGHT in mm"
        )
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("paper dimensions must be positive")
    return width, height


def parse_grid(value):
    """Parse a grid spec: "COLSxROWS", or "auto" to pack as many as fit."""
    if value.lower() == "auto":
        return None
    try:
        cols, rows = (int(part) for part in value.lower().split("x"))
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid grid {value!r}: use COLSxROWS")
    if cols < 1 or rows < 1:
        raise argparse.ArgumentTypeError("grid must be at least 1x1")
    return cols, rows


def positive(value):
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return number


def cell_dim(value):
    """A cell dimension in mm, or "auto" to scale the grid to the page."""
    if value.lower() == "auto":
        return None
    return positive(value)


def fit_grid(paper, cell):
    """Largest COLSxROWS grid of these cells that fits on the paper."""
    return max(1, int(paper[0] // cell[0])), max(1, int(paper[1] // cell[1]))


def cell_size(aspect, cols, rows, paper, width=None, height=None):
    """Cell size in mm, keeping the image aspect ratio (width / height).

    With an explicit width or height the other side follows from the aspect.
    With neither, the cell grows until the grid fills the page in one direction.
    """
    if width is not None and height is not None:
        return width, height
    if width is not None:
        return width, width / aspect
    if height is not None:
        return height * aspect, height

    width = min(paper[0] / cols, paper[1] / rows * aspect)
    return width, width / aspect


def render(
    image,
    output,
    paper,
    grid,
    cell,
    guides=True,
    guide_length=None,
    line_width=0.05,
    line_color=150,
):
    """Write the tiled PDF: one page, the image repeated over the grid."""
    cols, rows = grid
    cell_w, cell_h = cell
    offset_x = (paper[0] - cell_w * cols) / 2
    offset_y = (paper[1] - cell_h * rows) / 2

    pdf = FPDF(unit="mm", format=paper)
    pdf.set_auto_page_break(False, margin=0)
    pdf.set_margins(0, 0, 0)
    pdf.add_page()

    for col in range(cols):
        for row in range(rows):
            pdf.image(
                image,
                col * cell_w + offset_x,
                row * cell_h + offset_y,
                cell_w,
                cell_h,
            )

    if guides:
        pdf.set_line_width(line_width)
        pdf.set_draw_color(line_color)

        for col in range(cols + 1):
            x = col * cell_w + offset_x
            if guide_length is None:
                pdf.line(x, 0, x, paper[1])
            else:
                pdf.line(x, 0, x, guide_length)
                pdf.line(x, paper[1] - guide_length, x, paper[1])

        for row in range(rows + 1):
            y = row * cell_h + offset_y
            if guide_length is None:
                pdf.line(0, y, paper[0], y)
            else:
                pdf.line(0, y, guide_length, y)
                pdf.line(paper[0] - guide_length, y, paper[0], y)

    pdf.output(output)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="repeat4print",
        description="Tile an image across a sheet of paper as a print-ready PDF.",
    )
    parser.add_argument("image", help="image to repeat (PNG, JPEG or GIF)")
    parser.add_argument(
        "-o",
        "--output",
        default="result.pdf",
        help="output PDF path (default: %(default)s)",
    )
    parser.add_argument(
        "-p",
        "--paper",
        type=parse_paper,
        default="a3",
        help="paper size: a3, a4, a5, letter, or WIDTHxHEIGHT in mm (default: a3)",
    )
    parser.add_argument(
        "-l",
        "--landscape",
        action="store_true",
        help="rotate the paper to landscape",
    )
    parser.add_argument(
        "-g",
        "--grid",
        type=parse_grid,
        default="auto",
        help="repeats as COLSxROWS, or 'auto' to pack as many as fit "
        "(default: %(default)s)",
    )
    parser.add_argument(
        "--cell-width",
        type=cell_dim,
        default=UNSET,
        help="cell width in mm, or 'auto' to scale the grid to the page; "
        "height follows the image aspect ratio (default: 51)",
    )
    parser.add_argument(
        "--cell-height",
        type=cell_dim,
        help="cell height in mm; width follows the image aspect ratio. "
        "Overrides --cell-width unless that is given explicitly",
    )
    parser.add_argument(
        "--no-guides",
        dest="guides",
        action="store_false",
        help="omit the cutting guide lines",
    )
    parser.add_argument(
        "--guide-length",
        type=positive,
        help="draw guides as marks of this length (mm) at the page edges "
        "instead of full lines",
    )
    parser.add_argument(
        "--line-width",
        type=positive,
        default=0.05,
        help="guide line width in mm (default: %(default)s)",
    )
    parser.add_argument(
        "--line-color",
        type=int,
        default=150,
        help="guide line grey level, 0 black to 255 white (default: %(default)s)",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    # Defaults come in as strings, so the type= parsers never see them.
    paper = parse_paper(args.paper) if isinstance(args.paper, str) else args.paper
    grid = parse_grid(args.grid) if isinstance(args.grid, str) else args.grid
    if args.landscape:
        paper = (paper[1], paper[0])

    try:
        with Image.open(args.image) as image:
            aspect = image.width / image.height
    except (OSError, ValueError) as error:
        parser.error(f"cannot read {args.image}: {error}")

    cell_width = args.cell_width
    if cell_width is UNSET:
        cell_width = None if args.cell_height is not None else DEFAULT_CELL_WIDTH

    if grid is None and cell_width is None and args.cell_height is None:
        parser.error(
            "--grid auto needs a cell size: give --cell-width or --cell-height"
        )

    # An auto grid needs the cell size first; an auto cell needs the grid first.
    if grid is None:
        cell = cell_size(aspect, 1, 1, paper, cell_width, args.cell_height)
        grid = fit_grid(paper, cell)
    else:
        cell = cell_size(
            aspect, grid[0], grid[1], paper, cell_width, args.cell_height
        )

    cols, rows = grid
    if cell[0] * cols > paper[0] or cell[1] * rows > paper[1]:
        parser.error(
            f"a {cols}x{rows} grid of {cell[0]:.1f}x{cell[1]:.1f}mm cells "
            f"does not fit on {paper[0]:.0f}x{paper[1]:.0f}mm paper"
        )

    render(
        args.image,
        args.output,
        paper,
        grid,
        cell,
        guides=args.guides,
        guide_length=args.guide_length,
        line_width=args.line_width,
        line_color=args.line_color,
    )
    print(
        f"{args.output}: {cols}x{rows} of {cell[0]:.1f}x{cell[1]:.1f}mm "
        f"on {paper[0]:.0f}x{paper[1]:.0f}mm"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
