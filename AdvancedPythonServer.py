from flask import Flask, request, send_file, Response, render_template_string
import os

app = Flask(__name__)

# Configuration
DIRECTORY = '.'  # Directory to serve files from
CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB per chunk

@app.route('/')
def list_files():
    try:
        files = os.listdir(DIRECTORY)
        files = [f for f in files if os.path.isfile(os.path.join(DIRECTORY, f))]
        return render_template_string('''
            <h1>Available Files</h1>
            <ul>
                {% for file in files %}
                    <li><a href="{{ url_for('download_file', filename=file) }}">{{ file }}</a></li>
                {% endfor %}
            </ul>
        ''', files=files)
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    try:
        file_path = os.path.join(DIRECTORY, filename)
        
        if not os.path.isfile(file_path):
            return Response("File not found", status=404)

        file_size = os.path.getsize(file_path)
        range_header = request.headers.get('Range', None)
        byte_range = None

        if range_header:
            byte_range = range_header.strip().split('=')[1]
            byte_range = byte_range.split('-')
            byte_range = [int(x) if x else None for x in byte_range]

        def generate():
            with open(file_path, 'rb') as f:
                if byte_range:
                    start = byte_range[0]
                    end = byte_range[1] if byte_range[1] is not None else file_size - 1
                    f.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        chunk_size = min(CHUNK_SIZE, remaining)
                        data = f.read(chunk_size)
                        if not data:
                            break
                        remaining -= len(data)
                        yield data
                else:
                    while True:
                        data = f.read(CHUNK_SIZE)
                        if not data:
                            break
                        yield data

        if byte_range:
            start = byte_range[0]
            end = byte_range[1] if byte_range[1] is not None else file_size - 1
            content_length = end - start + 1
            return Response(generate(), 
                            status=206, 
                            mimetype='application/octet-stream',
                            headers={
                                'Content-Range': f'bytes {start}-{end}/{file_size}',
                                'Accept-Ranges': 'bytes',
                                'Content-Length': content_length,
                                'Content-Disposition': f'attachment; filename="{filename}"',
                            })
        else:
            return Response(generate(), 
                            status=200, 
                            mimetype='application/octet-stream',
                            headers={
                                'Content-Length': file_size,
                                'Content-Disposition': f'attachment; filename="{filename}"',
                            })

    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, threaded=True)
