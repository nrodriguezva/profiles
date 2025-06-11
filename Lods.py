def log_to_html(log_path, html_path):
    with open(log_path, 'r') as log_file:
        lines = log_file.readlines()

    with open(html_path, 'w') as html_file:
        html_file.write("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Log Report</title>
            <style>
                body { font-family: monospace; background-color: #f0f0f0; padding: 20px; }
                .info { color: blue; }
                .error { color: red; font-weight: bold; }
                .warning { color: orange; }
                .normal { color: #333; }
            </style>
        </head>
        <body>
            <h2>Log Report</h2>
            <pre>
        """)

        for line in lines:
            escaped_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            if 'ERROR' in line:
                html_file.write(f'<span class="error">{escaped_line}</span>')
            elif 'WARNING' in line:
                html_file.write(f'<span class="warning">{escaped_line}</span>')
            elif 'INFO' in line:
                html_file.write(f'<span class="info">{escaped_line}</span>')
            else:
                html_file.write(f'<span class="normal">{escaped_line}</span>')

        html_file.write("""
            </pre>
        </body>
        </html>
        """)

# Uso del script
log_to_html('archivo.log', 'reporte.html')
