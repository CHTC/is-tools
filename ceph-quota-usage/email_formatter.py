import csv
#
# This code was mostly shamelessly taken and repurposed from Jason Patton's JobAccounting reporting scripts.
#

def break_chars(s):
    # Break after [@_.]
    # Don't break after [-]
    zero_width_space = "&#8203;"
    non_breaking_hyphen = "&#8209;"
    for char in ["@", "_", "."]:
        s = s.replace(char, f"{char}{zero_width_space}")
    s = s.replace("-", non_breaking_hyphen)
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    return s


DEFAULT_TEXT_FORMAT    = lambda x: f'<td class="other">{break_chars(x)}</td>'
DEFAULT_NUMERIC_FORMAT = lambda x: f"<td class=\"numeric\">{int(x):,}</td>"
DEFAULT_COL_FORMATS    = {
    "Path" : lambda x: f"<td class=\"text\">{str(x)}</td>",
    "Byte Quota (Gibibytes)" : lambda x: f"<td class=\"numeric\">{float(x):.2f}</td>",
    "Byte Usage (Gibibytes)" : lambda x: f"<td class=\"numeric\">{float(x):.2f}</td>",
    "Percent Bytes Used (%)" : lambda x: f"<td class=\"numeric\">{float(x):.2f}</td>",
    "File Count Quota" : lambda x: f"<td class=\"numeric\">{int(x)}</td>",
    "File Count Usage" : lambda x: f"<td class=\"numeric\">{int(x)}</td>",
    "File Count Usage (%)" : lambda x: f"<td class=\"numeric\">{float(x):.2f}</td>",
    "Last Modified" : lambda x: f"<td class=\"text\">{str(x)}</td>",
    "Backing Pool" : lambda x: f"<td class=\"text\">{str(x)}</td>",
}

DEFAULT_STYLES = {
    "body": [
        "font-size: 11pt",
        "font-family: sans-serif"
        ],
    "h1": [
        "font-size: 12pt",
        "text-align: center",
        ],
    "table": [
        "font-size: 10pt",
        "border-collapse: collapse",
        "border-color: #ffffff",
        ],
    "tr.odd": ["background-color: #fee"],
    "tr.even": ["background-color: #fff"],
    "th": [
        "border: 1px solid black",
        "font-weight: bold",
        "text-align: center",
        "background-color: #ddd",
        "min-width: 1px",
        ],
    "td": [
        "border: 1px solid black",
        "text-align: left",
        "min-width: 1px",
        ],
    "td.text": ["text-align: left"],
    "td.numeric": ["text-align: right"],
    "td.other": ["text-align: right"],
}


class BaseFormatter:
    def __init__(self, table_files, *args, **kwargs):
        self.html_tables = []
        self.table_files = table_files
        for table_file in table_files:
            self.html_tables.append(self.get_table_html(table_file, **kwargs))

    def load_table(self, filename):
        with open(filename) as f:
            reader = csv.reader(f)
            header = [""] + next(reader)
            rows = [[""] + row for row in reader]
        data = {
            "header": header,
            "rows": rows,
        }
        return data

    def format_rows(self,
                    header,
                    rows,
                    custom_fmts={},
                    default_text_fmt=None,
                    default_numeric_fmt=None
                        ):
        fmts = DEFAULT_COL_FORMATS.copy()
        fmts.update(custom_fmts)
        if default_text_fmt is None:
            default_text_fmt = DEFAULT_TEXT_FORMAT
        if default_numeric_fmt is None:
            default_numeric_fmt = DEFAULT_NUMERIC_FORMAT

        rows = rows.copy()
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                col = header[j]

                # First column (blank header) contains row number
                if col == "" and value == "":
                    rows[i][j] = default_numeric_fmt(float(i+1))
                    continue

                # Any column with a numeric value < 0 is undefined
                try:
                    if float(value) < 0:
                        value = ""
                except ValueError:
                    pass

                # Try to format columns as numeric (or as defined
                # in fmts), otherwise it's a string
                if col in fmts:
                    try:
                        rows[i][j] = fmts[col](value)
                    except ValueError:
                        try:
                            rows[i][j] = fmts[col](float(value))
                        except ValueError:
                            rows[i][j] = default_text_fmt(value)
                else:
                    try:
                        rows[i][j] = default_numeric_fmt(float(value))
                    except ValueError:
                        rows[i][j] = default_text_fmt(value)

        return rows

    def get_table_title(self, table_file):
        return str(table_file).strip(".csv").replace("_", " ")

    def get_table_html(self, table_file, **kwargs):
        table_data = self.load_table(table_file)
        rows = self.format_rows(table_data["header"], table_data["rows"])

        rows_html = []
        for i, row in enumerate(rows):
            tr_class = ["even", "odd"][i % 2]
            rows_html.append(f'<tr class="{tr_class}">{"".join(row)}</tr>')

        newline = "\n  "
        html = f"""
<h1>{self.get_table_title(table_file)}</h1>
<table>
  <tr><th>{'</th><th>'.join(table_data['header'])}</th></tr>
  {newline.join(rows_html)}
</table>
"""
        return html

    def get_css(self, custom_styles={}):
        styles = DEFAULT_STYLES.copy()
        styles.update(custom_styles)

        style = "\n"
        newline_tab = "\n  "
        for tag, attrs in styles.items():
            attrs = [f"{attr};" for attr in attrs]
            style += f"{tag} {{\n  {newline_tab.join(attrs)}\n}}\n"

        return style

    def get_html(self):
        newline = "\n"
        html = f"""
<html>
<head>
<style>{self.get_css()}</style>
</head>
<body>
{newline.join(self.html_tables)}
</body>
</html>
"""
        return html
