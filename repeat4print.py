import sys

from fpdf import FPDF

if len(sys.argv) > 1:
    target = sys.argv[1]


paper_size = (420, 297)  # A3 landscape
# paper_size = (210, 297) # A4 portrait
rep_x, rep_y = 8, 8


pdf = FPDF(unit="mm", format=paper_size)
pdf.set_auto_page_break(False, margin=0)
pdf.set_margins(0, 0, 0)

pdf.add_page()

x_off = 51
y_off = 36
offset_x = (paper_size[0] - x_off * rep_x) / 2
offset_y = (paper_size[1] - y_off * rep_y) / 2

print(offset_x)

for x in range(0, rep_x):
    for y in range(0, rep_y):
        pdf.image(target, x * x_off + offset_x, y * y_off + offset_y, x_off, y_off)

line_h = -1

pdf.set_line_width(0.05)
pdf.set_draw_color(150)

# horizontal lines
for x in range(0, rep_x + 1):
    if line_h == -1:
        pdf.line(x * x_off + offset_x, 0, x * x_off + offset_x, paper_size[1])
    else:
        pdf.line(x * x_off + offset_x, 0, x * x_off + offset_x, line_h)
        pdf.line(
            x * x_off + offset_x,
            paper_size[1] - line_h,
            x * x_off + offset_x,
            paper_size[1],
        )

# vertical lines
for y in range(0, rep_y + 1):
    if line_h == -1:
        pdf.line(0, y * y_off + offset_y, paper_size[0], y * y_off + offset_y)
    else:
        pdf.line(0, y * y_off + offset_y, line_h, y * y_off + offset_y)
        pdf.line(
            paper_size[0] - line_h,
            y * y_off + offset_y,
            paper_size[0],
            y * y_off + offset_y,
        )


pdf.output("test.pdf")
