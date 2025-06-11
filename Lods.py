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
                body {
                    font-family: monospace;
                    background-color: #f0f0f0;
                    display: flex;
                    justify-content: center;
                    padding: 40px;
                }
                .container {
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    max-width: 90%;
                    word-wrap: break-word;
                    white-space: pre-wrap;
                }
                .info { color: blue; }
                .error { color: red; font-weight: bold; }
                .warning { color: orange; }
                .normal { color: #333; }
            </style>
        </head>
        <body>
            <div class="container">
        """)

        for line in lines:
            escaped_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            if 'ERROR' in line:
                html_file.write(f'<div class="error">{escaped_line}</div>\n')
            elif 'WARNING' in line:
                html_file.write(f'<div class="warning">{escaped_line}</div>\n')
            elif 'INFO' in line:
                html_file.write(f'<div class="info">{escaped_line}</div>\n')
            else:
                html_file.write(f'<div class="normal">{escaped_line}</div>\n')

        html_file.write("""
            </div>
        </body>
        </html>
        """)

# Uso del script
log_to_html('archivo.log', 'reporte.html')
